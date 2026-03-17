"""AI agent core: multi-step tool calling loop with SSE streaming."""

import json
from collections.abc import AsyncGenerator

from openai import AsyncOpenAI

from app.config import settings
from app.agent.tools import AGENT_TOOLS, MODULE_TOOLS
from app.services import (
    reconciliation_service,
    tax_service,
    report_service,
    cost_alloc_service,
)

SYSTEM_PROMPT = """你是星辰科技有限公司的AI财务助理，具备深厚的中国企业会计准则知识。

你可以帮助用户：
- 银行对账：查询流水、分析未匹配项、提供匹配建议
- 税务准备：查询申报数据、估算税额、校验合规性
- 财务报表：生成三大报表、计算财务指标、钻取明细
- 成本分摊：查询分摊结果、模拟不同方案、对比差异

请用中文回复，专业、简洁、准确。数字保留2位小数，金额单位为元。
如需数据支撑，主动调用工具获取。

【写操作规则】当需要执行写操作工具（auto_match_reconciliation、generate_tax_filing、run_cost_allocation）时，
必须先以 dry_run=true 调用，向用户展示操作摘要后询问"确认执行？"。
只有在对话历史中用户明确回复"确认"或"是"或"好的"或"执行"之后，才可以以 dry_run=false 真实写入。"""

WRITE_TOOL_MODULE = {
    "auto_match_reconciliation": "reconciliation",
    "generate_tax_filing": "tax",
    "run_cost_allocation": "cost_alloc",
}

MAX_ITERATIONS = 5


async def execute_tool(tool_name: str, tool_input: dict, session) -> str:
    try:
        if tool_name == "query_bank_transactions":
            result = await reconciliation_service.get_transactions(session, **{k: v for k, v in tool_input.items() if k in ("period", "min_amount", "max_amount", "counterparty")})
        elif tool_name == "query_book_entries":
            result = await reconciliation_service.get_book_entries(session, **{k: v for k, v in tool_input.items() if k in ("period", "account_code")})
        elif tool_name == "get_reconciliation_status":
            result = await reconciliation_service.get_reconciliation_status(session, period=tool_input.get("period"))
        elif tool_name == "analyze_unmatched_items":
            result = await reconciliation_service.get_unmatched(session, period=tool_input["period"])
        elif tool_name == "query_tax_data":
            result = await tax_service.get_filing(session, form_type=tool_input["form_type"], period=tool_input["period"])
        elif tool_name == "calculate_tax_estimate":
            result = await tax_service.get_estimate(session, period=tool_input["period"])
        elif tool_name == "check_tax_compliance":
            result = await tax_service.get_validation(session, form_type=tool_input["form_type"], period=tool_input["period"])
        elif tool_name == "generate_financial_report":
            await report_service.generate_reports(session, period=tool_input["period"])
            result = await report_service.get_report(session, report_type=tool_input.get("report_type", "balance_sheet"), period=tool_input["period"])
        elif tool_name == "calculate_financial_indicators":
            result = await report_service.get_indicators(session, period=tool_input["period"])
        elif tool_name == "drill_down_report_item":
            result = await report_service.drill_down(session, report_type=tool_input["report_type"], line_no=tool_input["line_no"], period=tool_input["period"], level=tool_input.get("level", 1))
        elif tool_name in ("query_cost_allocation", "compare_allocation_schemes"):
            result = await cost_alloc_service.get_results(session, period=tool_input["period"])
        elif tool_name == "simulate_allocation":
            result = await cost_alloc_service.simulate(session, period=tool_input["period"])
        elif tool_name == "auto_match_reconciliation":
            dry_run = tool_input.get("dry_run", True)
            result = await reconciliation_service.run_auto_match(session, tool_input["period"], dry_run=dry_run)
        elif tool_name == "generate_tax_filing":
            dry_run = tool_input.get("dry_run", True)
            result = await tax_service.generate_filing(session, tool_input["form_type"], tool_input["period"], dry_run=dry_run)
        elif tool_name == "run_cost_allocation":
            dry_run = tool_input.get("dry_run", True)
            result = await cost_alloc_service.calculate(session, tool_input["period"], save=not dry_run)
            result["dry_run"] = dry_run
        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"}, ensure_ascii=False)
        return json.dumps(result, ensure_ascii=False, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


async def chat_stream(
    message: str,
    module_context: str | None,
    history: list[dict],
    session,
) -> AsyncGenerator[str, None]:
    client = AsyncOpenAI(
        api_key=settings.volcengine_api_key,
        base_url=settings.volcengine_base_url,
    )

    tool_names = MODULE_TOOLS.get(module_context or "", []) if module_context else []
    tools = [t for t in AGENT_TOOLS if t["function"]["name"] in tool_names] if tool_names else AGENT_TOOLS

    messages = list(history) + [{"role": "user", "content": message}]
    # Ensure system prompt is first
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + [m for m in messages if m.get("role") != "system"]

    for _ in range(MAX_ITERATIONS):
        response = await client.chat.completions.create(
            model=settings.volcengine_model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )

        choice = response.choices[0]
        msg = choice.message

        if msg.content:
            yield json.dumps({"type": "text", "content": msg.content}, ensure_ascii=False)

        if not msg.tool_calls:
            break

        # Stream tool call events
        for tc in msg.tool_calls:
            tool_input = json.loads(tc.function.arguments)
            yield json.dumps({"type": "tool_call", "tool": tc.function.name, "input": tool_input}, ensure_ascii=False)

        # Append assistant turn (with tool_calls)
        messages.append(msg.model_dump(exclude_unset=True) | {"role": "assistant"})

        # Execute tools and append results
        for tc in msg.tool_calls:
            tool_input = json.loads(tc.function.arguments)
            result = await execute_tool(tc.function.name, tool_input, session)
            yield json.dumps({"type": "tool_result", "tool": tc.function.name, "result": json.loads(result)}, ensure_ascii=False)
            # Emit page_refresh after successful write (dry_run=False)
            if tc.function.name in WRITE_TOOL_MODULE and not tool_input.get("dry_run", True):
                yield json.dumps({"type": "page_refresh", "module": WRITE_TOOL_MODULE[tc.function.name]}, ensure_ascii=False)
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})

        if choice.finish_reason != "tool_calls":
            break

    yield json.dumps({"type": "done"}, ensure_ascii=False)
