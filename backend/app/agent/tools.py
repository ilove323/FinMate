"""Agent tool definitions — OpenAI function calling format."""

AGENT_TOOLS = [
    # Reconciliation
    {
        "type": "function",
        "function": {
            "name": "query_bank_transactions",
            "description": "查询银行流水记录，可按日期、金额范围、对方户名筛选",
            "parameters": {
                "type": "object",
                "properties": {
                    "period": {"type": "string", "description": "期间，格式 YYYY-MM"},
                    "min_amount": {"type": "number", "description": "最小金额"},
                    "max_amount": {"type": "number", "description": "最大金额"},
                    "counterparty": {"type": "string", "description": "对方户名关键词"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_book_entries",
            "description": "查询账簿记录/会计凭证，可按期间、科目筛选",
            "parameters": {
                "type": "object",
                "properties": {
                    "period": {"type": "string", "description": "期间，格式 YYYY-MM"},
                    "account_code": {"type": "string", "description": "科目编码前缀"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_reconciliation_status",
            "description": "获取银行对账匹配状态统计，包括匹配率、未匹配数量和金额",
            "parameters": {
                "type": "object",
                "properties": {
                    "period": {"type": "string", "description": "期间，格式 YYYY-MM"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_unmatched_items",
            "description": "获取未匹配项的详细分析，分为单边银行项和单边账簿项",
            "parameters": {
                "type": "object",
                "properties": {
                    "period": {"type": "string", "description": "期间，格式 YYYY-MM"},
                },
                "required": ["period"],
            },
        },
    },
    # Tax
    {
        "type": "function",
        "function": {
            "name": "query_tax_data",
            "description": "查询税务申报表数据，包括增值税和企业所得税",
            "parameters": {
                "type": "object",
                "properties": {
                    "form_type": {"type": "string", "description": "申报表类型: vat_general 或 cit_quarterly"},
                    "period": {"type": "string", "description": "期间，格式 YYYY-MM"},
                },
                "required": ["form_type", "period"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_tax_estimate",
            "description": "计算指定期间的预估税额，包括增值税和企业所得税",
            "parameters": {
                "type": "object",
                "properties": {
                    "period": {"type": "string", "description": "期间，格式 YYYY-MM"},
                },
                "required": ["period"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_tax_compliance",
            "description": "校验税务数据合规性，检查表内勾稽和合理性",
            "parameters": {
                "type": "object",
                "properties": {
                    "form_type": {"type": "string", "description": "申报表类型"},
                    "period": {"type": "string", "description": "期间"},
                },
                "required": ["form_type", "period"],
            },
        },
    },
    # Reports
    {
        "type": "function",
        "function": {
            "name": "generate_financial_report",
            "description": "生成指定期间的财务报表（资产负债表、利润表、现金流量表）",
            "parameters": {
                "type": "object",
                "properties": {
                    "period": {"type": "string", "description": "期间，格式 YYYY-MM"},
                    "report_type": {"type": "string", "description": "报表类型: balance_sheet, income, cash_flow"},
                },
                "required": ["period"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_financial_indicators",
            "description": "计算财务指标（流动比率、资产负债率、毛利率等）并评估健康度",
            "parameters": {
                "type": "object",
                "properties": {
                    "period": {"type": "string", "description": "期间，格式 YYYY-MM"},
                },
                "required": ["period"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "drill_down_report_item",
            "description": "钻取报表项目明细，从报表行项到科目余额再到凭证明细",
            "parameters": {
                "type": "object",
                "properties": {
                    "report_type": {"type": "string", "description": "报表类型"},
                    "line_no": {"type": "string", "description": "行号"},
                    "period": {"type": "string", "description": "期间"},
                    "level": {"type": "integer", "description": "钻取层级: 1=科目余额, 2=凭证明细"},
                },
                "required": ["report_type", "line_no", "period"],
            },
        },
    },
    # Cost allocation
    {
        "type": "function",
        "function": {
            "name": "query_cost_allocation",
            "description": "查询成本分摊数据，包括费用池、成本中心和分摊结果",
            "parameters": {
                "type": "object",
                "properties": {
                    "period": {"type": "string", "description": "期间，格式 YYYY-MM"},
                    "center_name": {"type": "string", "description": "成本中心名称"},
                },
                "required": ["period"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "simulate_allocation",
            "description": "模拟成本分摊计算（不保存结果），用于方案对比",
            "parameters": {
                "type": "object",
                "properties": {
                    "period": {"type": "string", "description": "期间"},
                },
                "required": ["period"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compare_allocation_schemes",
            "description": "对比不同分摊方案（如按人数vs按面积），展示差异",
            "parameters": {
                "type": "object",
                "properties": {
                    "period": {"type": "string", "description": "期间"},
                    "pool_name": {"type": "string", "description": "费用池名称"},
                },
                "required": ["period"],
            },
        },
    },
    # Write actions (dry_run=true 模拟, dry_run=false 真实写入)
    {
        "type": "function",
        "function": {
            "name": "auto_match_reconciliation",
            "description": "执行银行流水自动对账匹配。dry_run=true 时仅模拟不写入，返回预计匹配数量和金额摘要；dry_run=false 时真实写入匹配结果",
            "parameters": {
                "type": "object",
                "properties": {
                    "period": {"type": "string", "description": "期间，格式 YYYY-MM"},
                    "dry_run": {"type": "boolean", "description": "true=模拟预览，false=真实执行写入"},
                },
                "required": ["period", "dry_run"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_tax_filing",
            "description": "生成税务申报表数据。dry_run=true 时仅模拟不保存，返回将生成的行项目预览；dry_run=false 时真实生成并保存",
            "parameters": {
                "type": "object",
                "properties": {
                    "form_type": {"type": "string", "description": "申报表类型: vat_general 或 cit_quarterly"},
                    "period": {"type": "string", "description": "期间，格式 YYYY-MM"},
                    "dry_run": {"type": "boolean", "description": "true=模拟预览，false=真实执行写入"},
                },
                "required": ["form_type", "period", "dry_run"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_cost_allocation",
            "description": "执行成本分摊计算。dry_run=true 时仅模拟不保存，返回分摊结果预览；dry_run=false 时真实计算并保存",
            "parameters": {
                "type": "object",
                "properties": {
                    "period": {"type": "string", "description": "期间，格式 YYYY-MM"},
                    "dry_run": {"type": "boolean", "description": "true=模拟预览，false=真实执行写入"},
                },
                "required": ["period", "dry_run"],
            },
        },
    },
]

MODULE_TOOLS = {
    "reconciliation": ["query_bank_transactions", "query_book_entries", "get_reconciliation_status", "analyze_unmatched_items", "auto_match_reconciliation"],
    "tax": ["query_tax_data", "calculate_tax_estimate", "check_tax_compliance", "generate_tax_filing"],
    "reports": ["generate_financial_report", "calculate_financial_indicators", "drill_down_report_item"],
    "cost_alloc": ["query_cost_allocation", "simulate_allocation", "compare_allocation_schemes", "run_cost_allocation"],
}
