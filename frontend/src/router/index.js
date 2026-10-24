import { createRouter, createWebHistory } from 'vue-router'
import { isLoggedIn } from '../api'
//前端路由守卫相关
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import Sidebar from '../components/Sidebar.vue'
// 财务模块
import Receivable from '../views/finance/Receivable.vue'
import Payable from '../views/finance/Payable.vue'
import Voucher from '../views/finance/Voucher.vue'
import Ledger from '../views/finance/Ledger.vue'
import BudgetManage from '../views/finance/BudgetManage.vue'
import Reimburse from '../views/finance/Reimburse.vue'
import Report from '../views/finance/Report.vue'
// 智能审查模块
import InvoiceOcr from '../views/finance/InvoiceOcr.vue'
import InvoiceAudit from '../views/finance/InvoiceAudit.vue'
import AuditArchive from '../views/finance/AuditArchive.vue'

const routes = [
  {
    path: '/',
    redirect: '/login'//重定向到登录组件
  },
  {
    path: '/login',
    component: Login
  },
  {
    path: '/register',
    component: Register
  },
  {
    path: '/home',
    component: Sidebar,
    meta: { requiresAuth: true },//标记该组件需要登录才能记录
    children: [//定义子路由，服务于侧边栏的组件跳转
      { path: 'receivable', component: Receivable},
      { path: 'payable', component: Payable },
      { path: 'voucher', component: Voucher },
      { path: 'ledger', component: Ledger },
      { path: 'budget', component: BudgetManage },
      { path: 'reimburse', component: Reimburse },
      { path: 'report', component: Report },
      { path: 'invoice-ocr', component: InvoiceOcr },
      { path: 'invoice-audit', component: InvoiceAudit },
      { path: 'audit-archive', component: AuditArchive },
      { path: '', redirect: 'receivable' }//默认
    ]
  }
]

//创建路由对象的实例
const router = createRouter({
  history: createWebHistory(),//作用于URL的书写
  routes
})

//真正定义路由守卫规则：有 JWT 才能进入需要登录的页面
router.beforeEach((to, from, next) => {
  if (to.matched.some(record => record.meta.requiresAuth) && !isLoggedIn()) {
    next('/login')
  } else {
    next()
  }
})

//向其他组件暴露路由对象
export default router
