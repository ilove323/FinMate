"""AI agent core: multi-step tool_use loop with SSE streaming."""

import json
from collections.abc import AsyncGenerator

import anthropic

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
如需数据支撑，主动调用工具获取。"""

MAX_ITERATIONS = 5


async def execute_tool(tool_name: str, tool_input: dict, session) -> str:
    """Dispatch tool call to the appropriate service function."""
    try:
        if tool_name == "query_bank_transactions":
            result = await reconciliation_service.get_transactions(
                session,
                period=tool_input.get("period"),
                min_amount=tool_input.get("min_amount"),
                max_amount=tool_input.get("max_amount"),
                counterparty=tool_input.get("counterparty"),
            )
        elif tool_name == "query_book_entries":
            result = await reconciliation_service.get_book_entries(
                session,
                period=tool_input.get("period"),
                account_code=tool_input.get("account_code"),
            )
        elif tool_name == "get_reconciliation_status":
            result = await reconciliation_service.get_reconciliation_status(
                session,
                period=tool_input.get("period"),
            )
        elif tool_name == "analyze_unmatched_items":
            result = await reconciliation_service.get_unmatched(
                session, period=tool_input["period"]
            )
        elif tool_name == "query_tax_data":
            result = await tax_service.get_filing(
                session,
                form_type=tool_input["form_type"],
                period=tool_input["period"],
            )
        elif tool_name == "calculate_tax_estimate":
            result = await tax_service.get_estimate(session, period=tool_input["period"])
        elif tool_name == "check_tax_compliance":
            result = await tax_service.get_validation(
                session,
                form_type=tool_input["form_type"],
                period=tool_input["period"],
            )
        elif tool_name == "generate_financial_report":
            result = await report_service.get_report(
                session,
                report_type=tool_input.get("report_type", "balance_sheet"),
                period=tool_input["period"],
            )
        elif tool_name == "calculate_financial_indicators":
            result = await report_service.get_indicators(session, period=tool_input["period"])
        elif tool_name == "drill_down_report_item":
            result = await report_service.drill_down(
                session,
                report_type=tool_input["report_type"],
                line_no=tool_input["line_no"],
                period=tool_input["period"],
                level=tool_input.get("level", 1),
            )
        elif tool_name == "query_cost_allocation":
            result = await cost_alloc_service.get_results(
                session, period=tool_input["period"]
            )
        elif tool_name == "simulate_allocation":
            result = await cost_alloc_service.simulate(
                session, period=tool_input["period"]
            )
        elif tool_name == "compare_allocation_schemes":
            result = await cost_alloc_service.get_results(
                session, period=tool_input["period"]
            )
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
    """Multi-step agent loop; yields SSE-compatible JSON strings."""
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    # Select tools relevant to the current module context
    if module_context and module_context in MODULE_TOOLS:
        tool_names = MODULE_TOOLS[module_context]
        tools = [t for t in AGENT_TOOLS if t["name"] in tool_names]
    else:
        tools = AGENT_TOOLS

    messages: list[dict] = list(history)
    messages.append({"role": "user", "content": message})

    for iteration in range(MAX_ITERATIONS):
        response = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=tools,
            messages=messages,
        )

        # Collect text and tool_use blocks
        text_parts: list[str] = []
        tool_uses: list[dict] = []

        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_uses.append({"id": block.id, "name": block.name, "input": block.input})

        # Stream any text
        if text_parts:
            full_text = "".join(text_parts)
            yield json.dumps({"type": "text", "content": full_text}, ensure_ascii=False)

        # Stream tool calls and results
        if tool_uses:
            for tu in tool_uses:
                yield json.dumps(
                    {"type": "tool_call", "tool": tu["name"], "input": tu["input"]},
                    ensure_ascii=False,
                )

            # Execute tools and build tool_result block
            tool_results = []
            for tu in tool_uses:
                result_content = await execute_tool(tu["name"], tu["input"], session)
                tool_results.append(
                    {"type": "tool_result", "tool_use_id": tu["id"], "content": result_content}
                )
                # Parse result for streaming summary
                try:
                    parsed = json.loads(result_content)
                    yield json.dumps(
                        {"type": "tool_result", "tool": tu["name"], "result": parsed},
                        ensure_ascii=False,
                    )
                except Exception:
                    yield json.dumps(
                        {"type": "tool_result", "tool": tu["name"], "result": result_content},
                        ensure_ascii=False,
                    )

            # Append assistant turn and tool results to message history
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})

            # Continue loop for next assistant turn
            if response.stop_reason == "tool_use":
                continue

        # Stop when model signals end_turn or no more tool calls
        if response.stop_reason == "end_turn" or not tool_uses:
            break

    yield json.dumps({"type": "done"}, ensure_ascii=False)
