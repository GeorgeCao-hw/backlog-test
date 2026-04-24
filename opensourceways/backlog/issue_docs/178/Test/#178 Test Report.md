# #178 统一账号服务删除账号验证码验证 测试报告

## 1. 基本信息

* **需求链接**: [#178 统一账号服务需要在删除账号时通过邮箱/手机验证码进行验证](https://github.com/opensourceways/backlog/issues/178)
* **需求名称**: 统一账号服务删除账号增加邮箱/手机验证码验证
* **开发责任人**: Zherphy
* **测试责任人**: guoxiaozhen0304
* **最终结论：**： **通过** 
* **测试维度** ：
* [X] **功能自检测试**
* [X] **体验测试**
* [ ] **集成测试**
* [ ] **安全与隐私测试**
* [ ] **可靠性与韧性测试**
* [ ] **可服务性与可观测性测试**
* [ ] **性能与伸缩性测试**

## 2. 测试过程

### 2.1 功能测试专项

**1. OTP 发送接口正常流程验证**

* **对应 task 链接:** https://github.com/opensourceways/backlog/issues/178
* **测试步骤**: OTP 发送接口
* **预期结果**: 接口返回 200，邮箱收到 6 位数字验证码，Redis 中可查到对应 Key（TTL≤300s）。
* **测试结果**： **Passed** 
* **用例链接**：https://devcloud.cn-north-4.huaweicloud.com/cloudtestportal/project/2dbb0ac504234de39d622fdbcf814cf3/testsuite?branch_id=vd1k000115aohfnp&testplan_id=vd1t00011b8pv8kp

**2. OTP 正确校验后账号删除成功**

* **对应 task 链接:** https://github.com/opensourceways/backlog/issues/178
* **测试步骤**: OTP 发送接口
* **预期结果**: 接口返回 200，账号从数据库中删除，Redis OTP Key 同步销毁。
* **测试结果**： **Passed** 
* **用例链接**：https://devcloud.cn-north-4.huaweicloud.com/cloudtestportal/project/2dbb0ac504234de39d622fdbcf814cf3/testsuite?branch_id=vd1k000115aohfnp&testplan_id=vd1t00011b8pv8kp


**3. OTP 过期后拒绝删除**

* **对应 task 链接:** https://github.com/opensourceways/backlog/issues/178
* **测试步骤**: 过期后 OTP 发送接口
* **预期结果**: 接口返回 400 `invalid_otp`，账号未被删除。
* **测试结果**： **Passed** 
* **用例链接**：https://devcloud.cn-north-4.huaweicloud.com/cloudtestportal/project/2dbb0ac504234de39d622fdbcf814cf3/testsuite?branch_id=vd1k000115aohfnp&testplan_id=vd1t00011b8pv8kp


**4. 不携带 OTP 直接调用删除接口**

* **对应 task 链接:** https://github.com/opensourceways/backlog/issues/178
* **测试步骤**: 不携带 OTP 直接调用删除接口
* **预期结果**: 接口返回 400，拒绝执行删除。
* **测试结果**： **Passed** 
* **用例链接**：https://devcloud.cn-north-4.huaweicloud.com/cloudtestportal/project/2dbb0ac504234de39d622fdbcf814cf3/testsuite?branch_id=vd1k000115aohfnp&testplan_id=vd1t00011b8pv8kp


**5. 连续错误超 3 次锁定验证**

* **对应 task 链接:** https://github.com/opensourceways/backlog/issues/178
* **测试步骤**: 不连续错误超 3 次后，再次发送
* **预期结果**: 第 4 次调用返回 423，Redis OTP 记录被清除。
* **测试结果**： **Passed** 
* **用例链接**：https://devcloud.cn-north-4.huaweicloud.com/cloudtestportal/project/2dbb0ac504234de39d622fdbcf814cf3/testsuite?branch_id=vd1k000115aohfnp&testplan_id=vd1t00011b8pv8kp


### 2.2 体验测试专项

**1. 联系方式脱敏显示验证**

* **对应 task 链接:** https://github.com/opensourceways/backlog/issues/178
* **测试步骤**: 查看弹窗联系方式
* **预期结果**: 邮箱/手机号脱敏显示，不暴露完整信息。
* **测试结果**： **Passed** 
* **用例链接**：https://devcloud.cn-north-4.huaweicloud.com/cloudtestportal/project/2dbb0ac504234de39d622fdbcf814cf3/testsuite?branch_id=vd1k000115aohfnp&testplan_id=vd1t00011b8pv8kp


**2. 发送按钮冷却倒计时验证**

* **对应 task 链接:** https://github.com/opensourceways/backlog/issues/178
* **测试步骤**: 点击验证码发送按钮
* **预期结果**: 按钮进入不可点击状态并显示 60 秒倒计时，倒计时结束后恢复可点击。
* **测试结果**： **Passed** 
* **用例链接**：https://devcloud.cn-north-4.huaweicloud.com/cloudtestportal/project/2dbb0ac504234de39d622fdbcf814cf3/testsuite?branch_id=vd1k000115aohfnp&testplan_id=vd1t00011b8pv8kp


**3. 错误提示剩余次数展示**

* **对应 task 链接:** https://github.com/opensourceways/backlog/issues/178
* **测试步骤**: 输入错误验证码，查看是否有次数提示
* **预期结果**: 每次错误后提示剩余次数，锁定后提示重新发起。
* **测试结果**： **Passed** 
* **用例链接**：https://devcloud.cn-north-4.huaweicloud.com/cloudtestportal/project/2dbb0ac504234de39d622fdbcf814cf3/testsuite?branch_id=vd1k000115aohfnp&testplan_id=vd1t00011b8pv8kp




---

## 3. 测试结果汇总表

| 测试维度          | 用例总数 | 重点测试点描述                    | 通过数    | 不通过数   | 结论 (Pass/Fail) |
|---------------|------|------------------------------|--------|--------|----------------|
| **功能测试**      | 5    | OTP发送、校验、过期、缺失、锁定逻辑验证。      | 5 | 0 | Pass         |
| **体验测试**      | 3    | 脱敏展示、倒计时、错误次数提示。             | 3 | 0 | Pass         |

---

## 4. 遗留问题与风险说明

| 缺陷 ID         | 缺陷描述       | 严重程度 | 处理意见 (修复/忽略/转运维) |
|---------------|------------|------|------------------|
| -    | - | -    | -      |
