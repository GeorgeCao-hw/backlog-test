# #100 会议超时处理功能 测试报告

## 1. 基本信息

* **需求链接**: https://github.com/opensourceways/backlog/issues/100
* **需求名称**: 会议超时处理功能
* **开发责任人**: Tom_zc
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

**1.admin权限账号有社区管理页面**

* **对应task(issueID)链接: https://github.com/opensourceways/backlog/issues/100
* **测试步骤**:
  1. 使用admin权限账号登录，进入个人中心页面进行查看。
* **预期结果**: 有社区管理页面
* **测试结果**： Passed
* **用例链接**：https://devcloud.cn-north-4.huaweicloud.com/cloudtestportal/project/3a76c1785dda4b13a399937d1978f240/testsuite?branch_id=vd100000vt7dth64&testplan_id=vd1v00011b8q6e4h

**2.非admin权限账号有社区管理页面**

* **对应task(issueID)链接: https://github.com/opensourceways/backlog/issues/100
* **测试步骤**:
  1. 使用非admin权限账号登录，进入个人中心页面进行查看。
* **预期结果**: 无社区管理页面
* **测试结果**： Passed
* **用例链接**：https://devcloud.cn-north-4.huaweicloud.com/cloudtestportal/project/3a76c1785dda4b13a399937d1978f240/testsuite?branch_id=vd100000vt7dth64&testplan_id=vd1v00011b8q6e4h

**3.未到会议开始时间，会打上“未开始”的标签**

* **对应task(issueID)链接: https://github.com/opensourceways/backlog/issues/100
* **测试步骤**:
  1. 使用非admin权限账号登录，进入会议日历进行查看一个未到会议开始时间的会议。
* **预期结果**: 会议标题右方有“未开始”的标签
* **测试结果**： Passed
* **用例链接**：https://devcloud.cn-north-4.huaweicloud.com/cloudtestportal/project/3a76c1785dda4b13a399937d1978f240/testsuite?branch_id=vd100000vt7dth64&testplan_id=vd1v00011b8q6e4h

**4.已到会议开始时间，且未到结束时间，会打上“进行中”的标签**

* **对应task(issueID)链接: https://github.com/opensourceways/backlog/issues/100
* **测试步骤**:
  1. 使用非admin权限账号登录，进入会议日历进行查看一个已到会议开始时间且未到结束时间的会议。
* **预期结果**: 会议标题右方有“进行中”的标签
* **测试结果**： Passed
* **用例链接**：https://devcloud.cn-north-4.huaweicloud.com/cloudtestportal/project/3a76c1785dda4b13a399937d1978f240/testsuite?branch_id=vd100000vt7dth64&testplan_id=vd1v00011b8q6e4h

**5.已到会议结束时间但会议仍在进行，会打上“已超时”的标签**

* **对应task(issueID)链接: https://github.com/opensourceways/backlog/issues/100
* **测试步骤**:
  1. 使用非admin权限账号登录，进入会议日历进行查看一个到结束时间时会议仍在进行的会议。
* **预期结果**: 会议标题右方有“已超时”的标签
* **测试结果**： Passed
* **用例链接**：https://devcloud.cn-north-4.huaweicloud.com/cloudtestportal/project/3a76c1785dda4b13a399937d1978f240/testsuite?branch_id=vd100000vt7dth64&testplan_id=vd1v00011b8q6e4h

**6.admin账号结束一个会议后，会打上“已结束”的标签**

* **对应task(issueID)链接: https://github.com/opensourceways/backlog/issues/100
* **测试步骤**:
  1. 使用admin权限账号登录，进入社区会议管理页面，对一个已超时的会议点击“结束会议”按钮。
  2. 查看被结束的会议的标签
* **预期结果**: 会议标题右方有“已结束”的标签
* **测试结果**： Passed
* **用例链接**：https://devcloud.cn-north-4.huaweicloud.com/cloudtestportal/project/3a76c1785dda4b13a399937d1978f240/testsuite?branch_id=vd100000vt7dth64&testplan_id=vd1v00011b8q6e4h

**7.admin账号可以结束进行中的会议**

* **对应task(issueID)链接: https://github.com/opensourceways/backlog/issues/100
* **测试步骤**:
  1. 使用admin权限账号登录，进入社区会议管理页面，对一个进行中的会议点击“结束会议”按钮。
  2. 查看被结束的会议的标签
* **预期结果**: 会议标题右方有“已结束”的标签
* **测试结果**： Passed
* **用例链接**：https://devcloud.cn-north-4.huaweicloud.com/cloudtestportal/project/3a76c1785dda4b13a399937d1978f240/testsuite?branch_id=vd100000vt7dth64&testplan_id=vd1v00011b8q6e4h

**8.admin账号可以结束已超时的会议**

* **对应task(issueID)链接: https://github.com/opensourceways/backlog/issues/100
* **测试步骤**:
  1. 使用admin权限账号登录，进入社区会议管理页面，对一个已超时的会议点击“结束会议”按钮。
  2. 查看被结束的会议的标签
* **预期结果**: 会议标题右方有“已结束”的标签
* **测试结果**： Passed
* **用例链接**：https://devcloud.cn-north-4.huaweicloud.com/cloudtestportal/project/3a76c1785dda4b13a399937d1978f240/testsuite?branch_id=vd100000vt7dth64&testplan_id=vd1v00011b8q6e4h

**9.admin账号可以取消已结束和未开始的会议**

* **对应task(issueID)链接: https://github.com/opensourceways/backlog/issues/100
* **测试步骤**:
  1. 使用admin权限账号登录，进入社区会议管理页面，对一个已结束的会议点击“取消会议”按钮。
  2. 使用admin权限账号登录，进入社区会议管理页面，对一个未开始的会议点击“取消会议”按钮。
  3. 查看被结束的会议的标签
* **预期结果**: 社区会议管理页面对应的会议标题右方有“已取消”的标签
* **测试结果**： Passed
* **用例链接**：https://devcloud.cn-north-4.huaweicloud.com/cloudtestportal/project/3a76c1785dda4b13a399937d1978f240/testsuite?branch_id=vd100000vt7dth64&testplan_id=vd1v00011b8q6e4h

**10.已取消的会议不再在日历中显示数据**

* **对应task(issueID)链接: https://github.com/opensourceways/backlog/issues/100
* **测试步骤**:
  1. 使用admin权限账号登录，进入社区会议管理页面，对一个未开始的会议点击“取消会议”按钮。
  2. 查看会议日历
* **预期结果**: 会议日历中不再显示被取消的会议
* **测试结果**： Passed
* **用例链接**：https://devcloud.cn-north-4.huaweicloud.com/cloudtestportal/project/3a76c1785dda4b13a399937d1978f240/testsuite?branch_id=vd100000vt7dth64&testplan_id=vd1v00011b8q6e4h

**11.社区会议管理页面筛选和排序功能正常**

* **对应task(issueID)链接: https://github.com/opensourceways/backlog/issues/100
* **测试步骤**:
  1. 使用admin权限账号登录，进入社区会议管理页面，对发起人进行筛选，对状态进行筛选，对会议时间进行排序。
* **预期结果**: 筛选和排序功能正常
* **测试结果**： Passed
* **用例链接**：https://devcloud.cn-north-4.huaweicloud.com/cloudtestportal/project/3a76c1785dda4b13a399937d1978f240/testsuite?branch_id=vd100000vt7dth64&testplan_id=vd1v00011b8q6e4h

**12.若下一个会议开始半小时前仍有会议在进行，运营管理员会收到告警邮件**

* **对应task(issueID)链接: https://github.com/opensourceways/backlog/issues/100
* **测试步骤**:
  1. 创建两个时间间隔为半小时的会议，
  2. 若第一个会议过结束时间仍未结束，查看配置的运营管理员邮箱是否会收到提示邮件。
* **预期结果**: 会收到邮件
* **测试结果**： Passed
* **用例链接**：https://devcloud.cn-north-4.huaweicloud.com/cloudtestportal/project/3a76c1785dda4b13a399937d1978f240/testsuite?branch_id=vd100000vt7dth64&testplan_id=vd1v00011b8q6e4h

---

## 3. 测试结果汇总表

| 测试维度          | 用例总数   | 重点测试点描述             | 通过数    | 不通过数   | 结论 (Pass/Fail) |
|---------------|--------|---------------------|--------|--------|----------------|
| **功能测试**      | 12 | 覆盖核心业务逻辑与 API 契约。   | 12 | 0 | 通过         |

---

## 4. 遗留问题与风险说明

无
