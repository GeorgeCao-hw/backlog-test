# #1 [需求名称] 测试报告

## 1. 基本信息

* **需求链接**: https://github.com/opensourceways/backlog/issues/45
* **需求名称**: 社区管理员登录增加图形验证码功能
* **开发责任人**: KadenZhang3321
* **测试责任人**: guoxiaozhen0304
* **最终结论：**：通过
* **测试维度** ：
* [X] **功能自检测试**
* [ ] **体验测试**
* [ ] **集成测试**
* [ ] **安全与隐私测试**：
* [ ] **可靠性与韧性测试**
* [ ] **可服务性与可观测性测试**
* [ ] **性能与伸缩性测试**

## 2. 测试过程

### 2.1 功能测试专项

**1.登录失败达到阈值次数后，下次登录必须输入验证码**

* **对应task(issueID)链接: https://github.com/opensourceways/backlog/issues/45
* **测试步骤**:
  1. 使用账号登录，输入错误一次密码，查看是否会有验证码出现。
* **预期结果**: 输入错误一次密码，密码下方增加验证码输入框
* **测试结果**： Passed
* **用例链接**：https://devcloud.cn-north-4.huaweicloud.com/cloudtestportal/project/2dbb0ac504234de39d622fdbcf814cf3/testsuite?branch_id=vd1k000117ahg0nk&testplan_id=vd1j00011b8o7tbb

**2.验证码刷新功能正常**

* **对应task(issueID)链接: https://github.com/opensourceways/backlog/issues/45
* **测试步骤**:
  1. 使用账号登录，输入错误一次密码。
  2. 验证码图片右方点击刷新按钮
* **预期结果**: 验证码图片会刷新
* **测试结果**： Passed
* **用例链接**：https://devcloud.cn-north-4.huaweicloud.com/cloudtestportal/project/2dbb0ac504234de39d622fdbcf814cf3/testsuite?branch_id=vd1k000117ahg0nk&testplan_id=vd1j00011b8o7tbb

**3.输入正确的密码和验证码，可以登录成功**

* **对应task(issueID)链接: https://github.com/opensourceways/backlog/issues/45
* **测试步骤**:
  1. 使用账号登录，输入错误一次密码；
  2. 输入正确的密码，再输入正确的验证码，点击登录
* **预期结果**: 能够正常登录进入页面
* **测试结果**： Passed
* **用例链接**：https://devcloud.cn-north-4.huaweicloud.com/cloudtestportal/project/2dbb0ac504234de39d622fdbcf814cf3/testsuite?branch_id=vd1k000117ahg0nk&testplan_id=vd1j00011b8o7tbb

**4.输入错误的密码和正确的验证码，会提示用户错误次数后冻结账号**

* **对应task(issueID)链接: https://github.com/opensourceways/backlog/issues/45
* **测试步骤**:
  1. 使用账号登录，输入错误一次密码；
  2. 输入错误的密码，再输入正确的验证码，点击登录
* **预期结果**: 弹出提示框，提示还可以输入多少次密码后冻结账号
* **测试结果**： Passed
* **用例链接**：https://devcloud.cn-north-4.huaweicloud.com/cloudtestportal/project/2dbb0ac504234de39d622fdbcf814cf3/testsuite?branch_id=vd1k000117ahg0nk&testplan_id=vd1j00011b8o7tbb

---

## 3. 测试结果汇总表

| 测试维度          | 用例总数   | 重点测试点描述             | 通过数    | 不通过数   | 结论 (Pass/Fail) |
|---------------|--------|---------------------|--------|--------|----------------|
| **功能测试**      | 4 | 覆盖核心业务逻辑与 API 契约。   | 4 | 0 | 通过         |

---

## 4. 遗留问题与风险说明

无
