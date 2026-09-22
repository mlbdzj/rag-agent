"""Week2 Day6: 生成示例知识库语料

目的: 构造一个"像真实企业知识库"的混合格式语料, 覆盖 RAG 测试所需的场景:
  - 多格式: Markdown + PDF
  - 精确匹配: 产品型号 (SK-1000/2000/3000)、API 端点
  - 多跳/聚合: 定价跨套餐汇总、跨文档引用
  - 拒答: 语料里根本没有的信息

用法: uv run week02/make_corpus.py
产物: week02/data/raw/*.md, week02/data/raw/admin_guide.pdf
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).parent
RAW = ROOT / "data" / "raw"

DOCS: dict[str, str] = {
    "01_overview.md": """# 云雀 CRM 产品概述

云雀 CRM（Skylark CRM）是一套面向中小企业的客户关系管理 SaaS 系统，由云雀科技于 2019 年发布。产品口号是"让每一次客户接触都有记录"。

## 核心模块

云雀 CRM 由六个核心模块组成：

1. **线索管理（Leads）**：从官网、表单、广告等多渠道汇聚潜在客户。
2. **商机管理（Deals）**：跟踪销售漏斗，支持阶段自定义与赢单率预测。
3. **客户档案（Accounts）**：统一存储客户基本信息与往来记录。
4. **自动化工作流（Workflows）**：基于触发条件的自动任务与通知。
5. **报表中心（Reports）**：内置销售、活动、转化三大类报表。
6. **开放平台（Open API）**：供第三方系统集成的 REST API。

## 产品线

云雀 CRM 按部署形态分为三个产品线：

- **云雀标准版**：公有云 SaaS，多租户共享，开箱即用。
- **云雀企业版**：公有云独立实例，支持专属域名与更高配额。
- **云雀私有化（Skylark Private）**：部署在客户自有服务器，完全数据隔离。

## 技术架构

- 后端采用微服务架构，主要语言为 Go 与 Python。
- 数据库使用 PostgreSQL 作为主库，Redis 作为缓存。
- 全文检索基于 Elasticsearch，向量检索自 2023 年起引入 pgvector。
- 前端为 React 单页应用。

## 版本节奏

云雀 CRM 采用双月发布制，每年发布约 6 个功能版本。版本号遵循"主版本.次版本.修订号"语义化版本规范，例如 3.4.2。
""",
    "02_pricing.md": """# 云雀 CRM 定价与套餐

本文档列出云雀 CRM 各版本的计费方式与配额。价格为人民币含税价，按年付费有折扣。

## 标准版

- 基础价格：**299 元/用户/月**（按年付 8 折，即 239 元/用户/月）
- 包含：线索管理、商机管理、客户档案、基础报表
- 存储配额：每用户 5 GB 附件存储
- API 调用：每月 10 万次
- 不含自动化工作流与私有化部署

## 企业版

- 基础价格：**599 元/用户/月**（按年付 8 折，即 479 元/用户/月）
- 包含：标准版全部功能 + 自动化工作流 + 高级报表 + 专属域名
- 存储配额：每用户 20 GB 附件存储
- API 调用：每月 100 万次
- 支持 SSO 单点登录与审计日志

## 私有化版（Skylark Private）

- 授权费：**每年 30 万元起**，按部署规模与并发数报价
- 一次性实施费：8 万元（含部署、数据迁移、培训）
- 无用户数上限，但需购买对应规格的服务器
- 含 1 年原厂维保，续保为授权费的 15%/年

## 增值服务

- 数据迁移服务：2 万元/次（10 万条以内）
- 定制开发：3000 元/人天
- 专属客户成功经理：5 万元/年

## 折扣规则

- 按年付费统一 8 折。
- 一次性购买 100 席位以上，额外 9 折。
- 教育与非营利机构可申请 5 折优惠，需提供资质证明。
- 折扣可叠加，但总额不低于标价的 6 折。
""",
    "03_faq.md": """# 云雀 CRM 常见问题（FAQ）

## 账号与登录

**Q: 忘记密码怎么办？**
A: 在登录页点击"忘记密码"，通过注册邮箱或手机号重置。企业版用户也可联系管理员在后台重置。

**Q: 支持多少个用户同时在线？**
A: 标准版单租户默认支持 200 并发，企业版默认 1000 并发，可付费提升。私有化版取决于服务器规格。

**Q: 能否用微信扫码登录？**
A: 可以。企业版与私有化版支持企业微信、钉钉、微信三种扫码登录；标准版仅支持企业微信。

## 数据与安全

**Q: 我的数据存在哪里？**
A: 标准版与企业版数据存储在中国大陆的阿里云华东节点；私有化版存储在客户自有服务器。

**Q: 数据会用于训练 AI 模型吗？**
A: 不会。云雀科技承诺客户数据不用于任何模型训练，详见《安全与合规白皮书》。

**Q: 是否支持数据导出？**
A: 支持。管理员可在"设置-数据管理"中导出全量数据为 CSV 或 JSON，导出不额外收费。

## 功能相关

**Q: 自动化工作流支持哪些触发条件？**
A: 支持基于字段变更、时间（如创建后 3 天）、表单提交、API 调用四类触发条件。

**Q: 报表可以定时通过邮件发送吗？**
A: 企业版及以上支持。标准版只能在线查看与手动导出。

**Q: 是否支持多语言界面？**
A: 支持简体中文、繁体中文、英文、日文四种界面语言。

## 计费与合同

**Q: 可以按月付费吗？**
A: 可以。按月付费为标准价，按年付费享 8 折。

**Q: 试用期有多久？**
A: 标准版提供 14 天全功能免费试用；企业版提供 30 天试用，需商务对接。

**Q: 如何开具发票？**
A: 在"财务中心"提交开票申请，支持增值税普通发票与专用发票，一般 3 个工作日内寄出。

**Q: 能否退款？**
A: 未使用的整年订阅可在购买后 7 天内申请全额退款；已使用的不支持退款。
""",
    "04_api_spec.md": """# 云雀 CRM 开放 API 参考

开放 API 采用 REST 风格，基础地址为 `https://api.skylark-crm.com/v3`。所有请求需在 Header 携带 `Authorization: Bearer <token>`。

## 认证

- 获取 Token：`POST /oauth/token`，使用 client_id 与 client_secret 换取 access_token。
- Token 有效期 2 小时，需用 refresh_token 刷新。
- 私有化版的基础地址由客户自行配置，路径前缀同样为 `/v3`。

## 速率限制

| 套餐 | 默认 QPS | 每月调用上限 |
|------|---------|-------------|
| 标准版 | 5 | 10 万 |
| 企业版 | 50 | 100 万 |
| 私有化版 | 由服务器规格决定 | 无 |

超出速率限制时返回 HTTP 429，响应头 `Retry-After` 指明建议等待秒数。

## 主要端点

### 线索

- `GET /leads`：分页查询线索，支持 `status`、`owner_id`、`created_after` 过滤。
- `POST /leads`：创建线索。
- `PATCH /leads/{id}`：更新线索字段。
- `DELETE /leads/{id}`：删除线索（软删除，保留 30 天）。

### 商机

- `GET /deals`：查询商机列表。
- `POST /deals`：创建商机，必填 `account_id`、`amount`、`stage`。
- `POST /deals/{id}/stage`：推进商机阶段。

### 工作流

- `POST /workflows/{id}/trigger`：手动触发工作流，仅企业版及以上可用。

## 错误码

| 错误码 | 含义 | 处理建议 |
|--------|------|----------|
| 400 | 请求参数错误 | 检查字段类型与必填项 |
| 401 | 未认证或 Token 过期 | 刷新 Token |
| 403 | 无权限 | 检查账号角色 |
| 404 | 资源不存在 | 确认 ID |
| 429 | 触发速率限制 | 按 Retry-After 重试 |
| 500 | 服务端错误 | 稍后重试并联系支持 |

## Webhook

企业版支持 Webhook，可在"开放平台-Webhook"配置回调地址。事件类型包括 `lead.created`、`deal.won`、`deal.lost`。回调失败会重试 3 次，间隔分别为 1 分钟、5 分钟、30 分钟。
""",
    "05_security.md": """# 云雀 CRM 安全与合规白皮书（摘要）

## 数据加密

- 传输加密：全站强制 HTTPS（TLS 1.3）。
- 静态加密：数据库与对象存储均采用 AES-256 加密。
- 私有化版支持接入客户自有的 KMS 密钥管理服务。

## 权限模型

云雀 CRM 采用 RBAC（基于角色的访问控制）模型，内置五类角色：

1. **超级管理员**：拥有全部权限，可管理账号与计费。
2. **销售经理**：可查看团队全部数据，编辑商机。
3. **销售代表**：仅可查看与编辑自己负责的数据。
4. **市场人员**：可管理线索与营销活动，不可见成交金额。
5. **只读访客**：仅可查看被授权的报表。

支持自定义角色与字段级权限（企业版及以上）。

## 合规认证

- 已通过 **ISO 27001** 信息安全管理体系认证。
- 已通过 **等保三级** 备案（证书编号可向商务索取）。
- 遵循《个人信息保护法》，提供数据主体权利响应流程。

## 备份与可用性

- 标准版与企业版数据库每日全量备份，保留 30 天。
- 服务可用性 SLA：标准版 99.5%，企业版 99.9%，私有化版取决于客户运维。
- 故障恢复目标：RPO ≤ 1 小时，RTO ≤ 4 小时。

## 事件响应

发生安全事件时，云雀科技将在 4 小时内启动应急响应，并在 72 小时内向受影响客户通报。
""",
    "06_changelog.md": """# 云雀 CRM 版本更新日志

## v3.4.2（2024-11-15）
- 修复企业版 SSO 在部分 IdP 下登录失败的问题。
- 优化报表导出在大数据量下的内存占用。

## v3.4.0（2024-09-20）
- 新增"商机赢单率预测"，基于历史数据自动评分。
- 开放平台新增 `POST /deals/{id}/stage` 端点。
- 企业版支持字段级权限。

## v3.3.0（2024-07-12）
- 引入向量检索能力，用于"相似客户推荐"。
- 工作流新增"API 调用"触发条件。
- 修复 Webhook 在 HTTPS 证书过期时的重试异常。

## v3.2.0（2024-05-08）
- 线索管理支持自定义渠道来源。
- 新增日文界面。
- 私有化版支持接入客户 KMS。

## v3.0.0（2024-01-10）
- 架构升级，全面迁移至微服务。
- 报表中心重构，新增拖拽式报表。
- 停止支持 Internet Explorer。
""",
    "07_integration.md": """# 云雀 CRM 集成指南

云雀 CRM 可与多种第三方系统集成，集成方式分为官方连接器、开放 API、Webhook 三类。

## 官方连接器

以下系统提供开箱即用的官方连接器，无需开发：

- **企业微信**：同步组织架构，支持消息通知。
- **钉钉**：同步组织架构与审批流。
- **飞书**：同步日历与群消息通知。
- **腾讯会议**：会议与客户记录关联。

## 开放 API 集成

对于自研系统，推荐使用开放 API。典型场景：

- 将官网表单线索实时写入云雀 CRM。
- 将云雀 CRM 的成交数据同步到自建 BI 系统。

集成注意事项：
1. 先在"开放平台-应用管理"创建应用获取凭证。
2. 生产环境建议使用企业版以获得更高 QPS。
3. 务必实现指数退避重试以应对 429。

## Webhook 集成

Webhook 适用于"事件驱动"场景，例如商机赢单后自动通知外部系统。企业版及以上可用。

## 数据迁移

从其他 CRM（如销售易、纷享销客）迁移到云雀 CRM，可使用官方迁移工具或购买数据迁移服务。迁移支持客户、联系人、商机、活动四类对象。

## 常见集成问题

- **问：集成需要额外付费吗？**
  答：官方连接器免费；开放 API 按套餐配额；Webhook 仅企业版可用。
- **问：私有化版能否访问公网 API？**
  答：私有化版默认内网部署，如需公网访问需自行配置反向代理与安全策略。
""",
}

PDF_SECTIONS = [
    ("管理员手册 · 第一章 初始配置", """
首次部署云雀 CRM 后，超级管理员需要完成以下初始配置：

一、组织架构导入。在"设置-组织管理"中导入部门与员工，支持 CSV 批量导入。
二、角色分配。默认创建的五类角色需指派到具体员工。销售代表必须绑定所属团队，否则无法查看商机。
三、字段配置。可在"设置-对象管理"中自定义客户、线索、商机的字段，包括字段类型、是否必填、默认值。
四、审批流配置。企业版可配置商机折扣审批流，超过指定折扣需上级审批后方可推进阶段。
五、通知配置。配置站内信、邮件、企业微信三种通知渠道的开关。
"""),
    ("管理员手册 · 第二章 用户与权限", """
云雀 CRM 的权限体系分为三层：角色权限、数据范围、字段权限。

角色权限决定"能做什么操作"，例如创建商机、导出数据。数据范围决定"能看到谁的数据"，分为本人、本团队、本部门、全部四种。字段权限决定"能看哪些字段"，企业版以上可配置。

新增员工时，系统默认分配"销售代表"角色，数据范围为"本人"。管理员需根据实际情况调整。

员工离职时，建议先将其名下数据批量转交给接替人，再停用账号。停用账号不影响历史数据留存。
"""),
    ("管理员手册 · 第三章 数据备份与恢复", """
云雀 CRM 标准版与企业版由平台自动完成每日全量备份，保留 30 天。管理员无法手动触发备份，但可在"设置-数据管理"中导出快照。

私有化版的备份策略由客户自行制定。官方建议：
一、数据库采用流复制实现主从热备，RPO 可控制在秒级。
二、对象存储启用跨区域复制。
三、每季度做一次恢复演练，验证备份可用性。

恢复操作属于高风险操作，需至少两名管理员双重确认。平台侧恢复请求通过工单提交，一般 4 小时内响应。
"""),
    ("管理员手册 · 第四章 计费与席位管理", """
套餐席位按"活跃用户"计费。活跃用户指过去 30 天内登录过的账号。

管理员可在"财务中心-席位管理"查看当前活跃用户数，并设置自动扩容上限，避免超额产生费用。

席位变更规则：
一、新增席位立即生效，费用按剩余周期折算。
二、减少席位在下一个计费周期生效，当期不退费。
三、从标准版升级到企业版，差价按剩余天数折算，功能立即解锁。

发票申请、合同下载、续费提醒均在财务中心统一管理。续费提醒默认提前 30 天发送给超级管理员与财务联系人。
"""),
    ("管理员手册 · 第五章 常见运维问题", """
问：系统提示"配额已用尽"怎么办？
答：检查是存储配额还是 API 配额。存储配额可在财务中心扩容；API 配额超限可升级套餐或优化调用频率。

问：如何排查集成接口返回 401？
答：401 表示未认证或 Token 过期。请确认 access_token 未过期（有效期 2 小时），并在过期前用 refresh_token 刷新。

问：私有化版升级需要停机吗？
答：小版本升级通常无需停机；大版本升级建议在业务低峰期进行，并提前备份数据库。

问：日志保留多久？
答：操作日志保留 180 天，登录日志保留 90 天。私有化版可由客户自行配置保留策略。
"""),
]


def write_markdown() -> None:
    for name, content in DOCS.items():
        (RAW / name).write_text(content, encoding="utf-8")
        print(f"  写入 {name} ({len(content)} 字符)")


def write_pdf() -> None:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
    from reportlab.lib.styles import ParagraphStyle

    # 尽量注册中文字体 (Windows 自带)
    font_name = "Helvetica"
    for candidate in (r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simsun.ttc", r"C:\Windows\Fonts\simhei.ttf"):
        if Path(candidate).exists():
            try:
                pdfmetrics.registerFont(TTFont("CN", candidate))
                font_name = "CN"
                break
            except Exception:  # noqa: BLE001
                continue

    style = ParagraphStyle("cn", fontName=font_name, fontSize=11, leading=18)
    title_style = ParagraphStyle("h", fontName=font_name, fontSize=15, leading=22, spaceAfter=10)

    doc_path = RAW / "admin_guide.pdf"
    doc = SimpleDocTemplate(str(doc_path), pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm)
    story = []
    for title, body in PDF_SECTIONS:
        story.append(Paragraph(title, title_style))
        for para in body.strip().split("\n"):
            if para.strip():
                story.append(Paragraph(para.strip(), style))
                story.append(Spacer(1, 6))
        story.append(Spacer(1, 18))
    doc.build(story)
    size = doc_path.stat().st_size
    print(f"  写入 admin_guide.pdf ({len(PDF_SECTIONS)} 章, {size} 字节, 字体={font_name})")


def main() -> None:
    if RAW.exists():
        shutil.rmtree(RAW)
    RAW.mkdir(parents=True, exist_ok=True)
    print(f"生成语料到: {RAW}")
    write_markdown()
    write_pdf()
    total_md = sum(len(c) for c in DOCS.values())
    print(f"\n完成: {len(DOCS)} 个 Markdown + 1 个 PDF, 文本合计约 {total_md:,} 字符")


if __name__ == "__main__":
    main()
