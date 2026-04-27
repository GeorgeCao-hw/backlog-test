# #1 openUBMC 新增开源实习页面 测试报告

## 1. 基本信息

* **需求链接**: https://github.com/opensourceways/backlog/issues/111
* **需求名称**: openUBMC 新增开源实习页面
* **开发责任人**: sky-winter
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

**1.能够正常进入开源实习页面**

* **对应task(issueID)链接: https://github.com/opensourceways/backlog/issues/111
* **测试步骤**:
  1. 进入openUBMC首页，在导航栏依次点击学习——开源实习，查看页面。
* **预期结果**: 能够正常进入开源实习页面，且页面符合高保真设计
* **测试结果**： Passed
* **用例链接**：https://devcloud.cn-north-4.huaweicloud.com/cloudtestportal/project/2ba87e228fdb464883efc24f85c0cc24/testsuite?branch_id=vd1k00011bb8itl8&testplan_id=vd1k00011bb8itmj&suite_id=vd1t00011bb8ousm&detail=base

**2.开源实习页面反馈功能正常**

* **对应task(issueID)链接: https://github.com/opensourceways/backlog/issues/111
* **测试步骤**:
  1. 进入openUBMC首页，在导航栏依次点击学习——开源实习。
  2. 在页面右方点击页面推荐按钮
* **预期结果**: 提示是反馈开源实习页面，且反馈功能正常。
* **测试结果**： Passed
* **用例链接**：https://devcloud.cn-north-4.huaweicloud.com/cloudtestportal/project/2ba87e228fdb464883efc24f85c0cc24/testsuite?branch_id=vd1k00011bb8itl8&testplan_id=vd1k00011bb8itmj&suite_id=vd1t00011bb8ousm&detail=base
**3.开源实习页面邮箱链接点击后可跳转至浏览器默认打开邮箱的页面**

* **对应task(issueID)链接: https://github.com/opensourceways/backlog/issues/111
* **测试步骤**:
  1. 进入openUBMC首页，在导航栏依次点击学习——开源实习。
  2. 在页面活动介绍下点击报名邮箱“contact@openubmc.cn”
  3. 在积分与激励规则下点击报名邮箱“contact@openubmc.cn”
* **预期结果**: 跳转至浏览器默认打开邮箱的页面
* **测试结果**： Passed
* **用例链接**：https://devcloud.cn-north-4.huaweicloud.com/cloudtestportal/project/2ba87e228fdb464883efc24f85c0cc24/testsuite?branch_id=vd1k00011bb8itl8&testplan_id=vd1k00011bb8itmj&suite_id=vd1t00011bb8ousm&detail=base

**4.开源实习页面所有实习任务的跳转链接跳转正确**

* **对应task(issueID)链接: https://github.com/opensourceways/backlog/issues/111
* **测试步骤**:
  1. 进入openUBMC首页，在导航栏依次点击学习——开源实习。
  2. 在活动介绍下的申请实习中点击“实习测试任务”
  3. 在实习任务下点击所有任务跳转链接
* **预期结果**: 所有实习任务的跳转链接跳转正确
* **测试结果**： Passed
* **用例链接**：https://devcloud.cn-north-4.huaweicloud.com/cloudtestportal/project/2ba87e228fdb464883efc24f85c0cc24/testsuite?branch_id=vd1k00011bb8itl8&testplan_id=vd1k00011bb8itmj&suite_id=vd1t00011bb8ousm&detail=base

**5.实习申请材料模板可以正常下载，且解压缩后的文件是相关模板文件**

* **对应task(issueID)链接: https://github.com/opensourceways/backlog/issues/111
* **测试步骤**:
  1. 进入openUBMC首页，在导航栏依次点击学习——开源实习。
  2. 在活动介绍下的申请实习中点击“实习申请材料模板”
* **预期结果**: 模板可以正常下载，且解压缩后的文件是相关模板文件
* **测试结果**： Passed
* **用例链接**：https://devcloud.cn-north-4.huaweicloud.com/cloudtestportal/project/2ba87e228fdb464883efc24f85c0cc24/testsuite?branch_id=vd1k00011bb8itl8&testplan_id=vd1k00011bb8itmj&suite_id=vd1t00011bb8ousm&detail=base

**6.实习任务认领邮件模板可以正常下载，且解压缩后的文件是相关模板文件**

* **对应task(issueID)链接: https://github.com/opensourceways/backlog/issues/111
* **测试步骤**:
  1. 进入openUBMC首页，在导航栏依次点击学习——开源实习。
  2. 在活动介绍下的领取任务中点击“实习任务认领邮件模板”
* **预期结果**: 模板可以正常下载，且解压缩后的文件是相关模板文件
* **测试结果**： Passed
* **用例链接**：https://devcloud.cn-north-4.huaweicloud.com/cloudtestportal/project/2ba87e228fdb464883efc24f85c0cc24/testsuite?branch_id=vd1k00011bb8itl8&testplan_id=vd1k00011bb8itmj&suite_id=vd1t00011bb8ousm&detail=base

**7.实习生证明资料和邮件模板可以正常下载，且解压缩后的文件是相关模板文件**

* **对应task(issueID)链接: https://github.com/opensourceways/backlog/issues/111
* **测试步骤**:
  1. 进入openUBMC首页，在导航栏依次点击学习——开源实习。
  2. 在活动介绍下的工资与证书发放中点击“实习生证明资料和邮件模板”
* **预期结果**: 模板可以正常下载，且解压缩后的文件是相关模板文件
* **测试结果**： Passed
* **用例链接**：https://devcloud.cn-north-4.huaweicloud.com/cloudtestportal/project/2ba87e228fdb464883efc24f85c0cc24/testsuite?branch_id=vd1k00011bb8itl8&testplan_id=vd1k00011bb8itmj&suite_id=vd1t00011bb8ousm&detail=base

---

## 3. 测试结果汇总表

| 测试维度          | 用例总数   | 重点测试点描述             | 通过数    | 不通过数   | 结论 (Pass/Fail) |
|---------------|--------|---------------------|--------|--------|----------------|
| **功能测试**      | 7 | 覆盖核心业务逻辑与 API 契约。   | 7 | 0 | 通过         |

---

## 4. 遗留问题与风险说明

无
