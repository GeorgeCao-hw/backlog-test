# #178 统一账号服务删除账号验证码验证 测试报告

## 1. 基本信息

* **需求链接**: [#178 统一账号服务需要在删除账号时通过邮箱/手机验证码进行验证](https://github.com/opensourceways/backlog/issues/178)
* **需求名称**: 统一账号服务删除账号增加邮箱/手机验证码验证
* **开发责任人**: Zherphy
* **测试责任人**: guoxiaozhen0304
* **最终结论：**： **[TODO]**  (通过 / 风险通过 / 不通过)
* **测试维度** ：
* [X] **功能自检测试**
* [X] **体验测试**
* [X] **集成测试**
* [X] **安全与隐私测试**
* [ ] **可靠性与韧性测试**
* [ ] **可服务性与可观测性测试**
* [ ] **性能与伸缩性测试**

## 2. 测试过程

### 2.1 功能测试专项

**1. OTP 发送接口正常流程验证**

* **对应 task 链接:** https://github.com/opensourceways/backlog/issues/178
* **预期结果**: 接口返回 200，邮箱收到 6 位数字验证码，Redis 中可查到对应 Key（TTL≤300s）。
* **测试结果**： **[TODO]** （Passed/Failed）
* **证明截图**: **[TODO]**

**2. OTP 正确校验后账号删除成功**

* **对应 task 链接:** https://github.com/opensourceways/backlog/issues/178
* **预期结果**: 接口返回 200，账号从数据库中删除，Redis OTP Key 同步销毁。
* **测试结果**： **[TODO]** （Passed/Failed）
* **证明截图**: **[TODO]**

**3. OTP 过期后拒绝删除**

* **对应 task 链接:** https://github.com/opensourceways/backlog/issues/178
* **预期结果**: 接口返回 400 `invalid_otp`，账号未被删除。
* **测试结果**： **[TODO]** （Passed/Failed）
* **证明截图**: **[TODO]**

**4. 不携带 OTP 直接调用删除接口**

* **对应 task 链接:** https://github.com/opensourceways/backlog/issues/178
* **预期结果**: 接口返回 400，拒绝执行删除。
* **测试结果**： **[TODO]** （Passed/Failed）
* **证明截图**: **[TODO]**

**5. 连续错误超 3 次锁定验证**

* **对应 task 链接:** https://github.com/opensourceways/backlog/issues/178
* **预期结果**: 第 4 次调用返回 423，Redis OTP 记录被清除。
* **测试结果**： **[TODO]** （Passed/Failed）
* **证明截图**: **[TODO]**

### 2.2 体验测试专项

**1. 联系方式脱敏显示验证**

* **对应 task 链接:** https://github.com/opensourceways/backlog/issues/178
* **预期结果**: 邮箱/手机号脱敏显示，不暴露完整信息。
* **测试结果**： **[TODO]** （Passed/Failed）
* **证明截图**: **[TODO]**

**2. 发送按钮冷却倒计时验证**

* **对应 task 链接:** https://github.com/opensourceways/backlog/issues/178
* **预期结果**: 按钮进入不可点击状态并显示 60 秒倒计时，倒计时结束后恢复可点击。
* **测试结果**： **[TODO]** （Passed/Failed）
* **证明截图**: **[TODO]**

**3. 错误提示剩余次数展示**

* **对应 task 链接:** https://github.com/opensourceways/backlog/issues/178
* **预期结果**: 每次错误后提示剩余次数，锁定后提示重新发起。
* **测试结果**： **[TODO]** （Passed/Failed）
* **证明截图**: **[TODO]**

### 2.3 集成测试专项

**1. 端到端删除全链路验证**

* **对应 task 链接:** https://github.com/opensourceways/backlog/issues/178
* **预期结果**: 全链路无报错，账号数据删除，前端跳转完成页，Redis Key 清除。
* **测试结果**： **[TODO]** （Passed/Failed）
* **证明截图**: **[TODO]**

**2. 通知服务对接验证**

* **对应 task 链接:** https://github.com/opensourceways/backlog/issues/178
* **预期结果**: 邮件和短信渠道均可正常收到 OTP，响应时间 ≤ 3s。
* **测试结果**： **[TODO]** （Passed/Failed）
* **证明截图**: **[TODO]**

**3. Redis OTP 状态一致性验证**

* **对应 task 链接:** https://github.com/opensourceways/backlog/issues/178
* **预期结果**: 并发场景下同一时刻只有一个有效 OTP，无竞争条件状态错误。
* **测试结果**： **[TODO]** （Passed/Failed）
* **证明截图**: **[TODO]**

### 2.4 安全与隐私测试专项

**1. OTP 日志脱敏验证**

* **对应 task 链接:** https://github.com/opensourceways/backlog/issues/178
* **预期结果**: 日志中不出现 OTP 明文，字段显示为 `***` 或不记录。
* **测试结果**： **[TODO]** （Passed/Failed）
* **证明截图**: **[TODO]**

**2. Redis OTP 存储安全验证**

* **对应 task 链接:** https://github.com/opensourceways/backlog/issues/178
* **预期结果**: Redis 存储为 HMAC-SHA256 哈希，不可还原明文 OTP。
* **测试结果**： **[TODO]** （Passed/Failed）
* **证明截图**: **[TODO]**

**3. OTP 一次性使用验证**

* **对应 task 链接:** https://github.com/opensourceways/backlog/issues/178
* **预期结果**: 第二次使用相同 OTP 返回 400，不可重放。
* **测试结果**： **[TODO]** （Passed/Failed）
* **证明截图**: **[TODO]**

**4. 鉴权绕过测试**

* **对应 task 链接:** https://github.com/opensourceways/backlog/issues/178
* **预期结果**: 无 Token 或过期 Token 均返回 401 Unauthorized。
* **测试结果**： **[TODO]** （Passed/Failed）
* **证明截图**: **[TODO]**

**5. 跨用户越权操作验证**

* **对应 task 链接:** https://github.com/opensourceways/backlog/issues/178
* **预期结果**: 返回 403 Forbidden，目标账号数据不受影响。
* **测试结果**： **[TODO]** （Passed/Failed）
* **证明截图**: **[TODO]**

**6. API 响应隐私验证**

* **对应 task 链接:** https://github.com/opensourceways/backlog/issues/178
* **预期结果**: 响应体中不包含用户完整邮箱或手机号。
* **测试结果**： **[TODO]** （Passed/Failed）
* **证明截图**: **[TODO]**

---

## 3. 测试结果汇总表

| 测试维度          | 用例总数 | 重点测试点描述                    | 通过数    | 不通过数   | 结论 (Pass/Fail) |
|---------------|------|------------------------------|--------|--------|----------------|
| **功能测试**      | 5    | OTP发送、校验、过期、缺失、锁定逻辑验证。      | [TODO] | [TODO] | [TODO]         |
| **体验测试**      | 3    | 脱敏展示、倒计时、错误次数提示。             | [TODO] | [TODO] | [TODO]         |
| **集成测试**      | 3    | 端到端删除链路、通知服务对接、Redis一致性。    | [TODO] | [TODO] | [TODO]         |
| **安全与隐私测试**   | 6    | 日志脱敏、哈希存储、一次性使用、鉴权、越权、响应隐私。 | [TODO] | [TODO] | [TODO]         |
| **可靠性与韧性**    | -    | 不涉及。                         | -      | -      | N/A            |
| **可服务性与可观测性** | -    | 不涉及。                         | -      | -      | N/A            |
| **性能与可伸缩性**   | -    | 不涉及。                         | -      | -      | N/A            |

---

## 4. 遗留问题与风险说明

| 缺陷 ID         | 缺陷描述       | 严重程度 | 处理意见 (修复/忽略/转运维) |
|---------------|------------|------|------------------|
| **[TODO]**    | **[TODO]** | -    | **[TODO]**       |
