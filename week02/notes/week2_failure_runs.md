# Week2 失败模式测试结果

## [fact] 云雀 CRM 有哪些核心模块?

- 检索来源: 01_overview.md, 05_security.md, 01_overview.md, 02_pricing.md, 07_integration.md

- 回答: 云雀 CRM 有六个核心模块[1]：

1. **线索管理（Leads）**：从官网、表单、广告等多渠道汇聚潜在客户[1]。
2. **商机管理（Deals）**：跟踪销售漏斗，支持阶段自定义与赢单率预测[1]。
3. **客户档案（Accounts）**：统一存储客户基本信息与往来记录[1]。
4. **自动化工作流（Workflows）**：基于触发条件的自动任务与通知[1]。
5. **报表中心（Reports）**：内置销售、活动、转化三大类报表[1]。
6. **开放平台（Open API）**：供第三方系统集成的 REST API[1]。

## [fact] 企业版每月多少钱?

- 检索来源: 02_pricing.md, 02_pricing.md, 03_faq.md, 05_security.md, 03_faq.md

- 回答: 企业版每月 599 元/用户/月（按年付 8 折，即 479 元/用户/月）[1]。

## [list] 云雀 CRM 通过了哪些合规认证?

- 检索来源: 05_security.md, 05_security.md, 02_pricing.md, 01_overview.md, 01_overview.md

- 回答: 云雀 CRM 已通过的合规认证包括：ISO 27001 信息安全管理体系认证、等保三级备案（证书编号可向商务索取），并遵循《个人信息保护法》，提供数据主体权利响应流程[2]。

## [aggregate] 标准版和企业版的 API 调用配额分别是多少?

- 检索来源: 03_faq.md, 02_pricing.md, 05_security.md, admin_guide.pdf, 01_overview.md

- 回答: 标准版每月 10 万次 API 调用[2]，企业版每月 100 万次[2]。

## [aggregate] 一次性购买 100 席位以上, 折扣最多能叠加到几折?

- 检索来源: 02_pricing.md, admin_guide.pdf, 03_faq.md, admin_guide.pdf, 02_pricing.md

- 回答: 一次性购买 100 席位以上，可在按年付费 8 折基础上额外 9 折，但折扣叠加后总额不低于标价的 6 折，即最多能叠加到 6 折[1]。

## [table] API 的默认 QPS 速率限制是多少?

- 检索来源: 04_api_spec.md, 07_integration.md, 04_api_spec.md, 03_faq.md, 05_security.md

- 回答: API 默认 QPS 速率限制按套餐区分：标准版 5 QPS，企业版 50 QPS，私有化版由服务器规格决定[1]。

## [keyword] 私有化版(Skylark Private)的 API 配额是多少?

- 检索来源: 02_pricing.md, 07_integration.md, 04_api_spec.md, 01_overview.md, 03_faq.md

- 回答: 资料中未找到相关信息。

资料中仅提到私有化版的基础地址由客户自行配置、路径前缀为 `/v3`[3]，以及私有化版默认内网部署[2]，但未提及私有化版的 API 配额。

## [multihop] 如果企业版用户忘记密码, 应该怎么处理?

- 检索来源: 03_faq.md, admin_guide.pdf, 04_api_spec.md, 05_security.md, admin_guide.pdf

- 回答: 企业版用户忘记密码时，可在登录页点击"忘记密码"，通过注册邮箱或手机号重置；也可联系管理员在后台重置[1]。

## [reject] 云雀 CRM 支持苹果手机的指纹登录吗?

- 检索来源: 03_faq.md, 01_overview.md, 06_changelog.md, 05_security.md, 04_api_spec.md

- 回答: 资料中未找到相关信息。

## [reject] 云雀 CRM 的 CEO 是谁?

- 检索来源: 01_overview.md, 05_security.md, 01_overview.md, 02_pricing.md, 04_api_spec.md

- 回答: 资料中未找到相关信息。
