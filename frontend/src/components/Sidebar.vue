<template>
  <div class="layout">
    <div class="sidebar">
      <div class="logo" v-once>ERP 财务系统</div>
      <div class="menu-list">
        <template v-for="(items, group) in groupedMenu" :key="group">
          <div class="menu-group-title">{{ group }}</div>
          <div 
          class="menu-item"
          :class="{active: activePath === item.path}"
          v-for="item in items"
          :key="item.path"
          @click="go(item.path)"
          ><!--:key相当于给每个item一个id-->
          <!--遍历 menuList → 为每个元素生成一个独立的 <div> → 每个 div 都绑定自己的 @click-->
          {{item.title}}
          </div>
        </template>
      </div>
      <div class="logout" @click="logout">退出登录</div>
    </div>
    <div class="main-content">
      <div class="content-box">
        <router-view />
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter, useRoute } from 'vue-router'
import { ref, watch, computed } from 'vue'
import { clearSession, getUser } from '../api'

const router = useRouter()
const route = useRoute()//获取当前页面路由信息 → 拿地址、参数、路径

const activePath = ref('')

// 性能优化：菜单数据无需响应式 → markRaw
const menuList = [
  { title: '应收管理', path: '/home/receivable', group: '财务模块', financeOnly: true },
  { title: '应付管理', path: '/home/payable', group: '财务模块', financeOnly: true },
  { title: '费用报销', path: '/home/reimburse', group: '财务模块' },
  { title: '凭证生成', path: '/home/voucher', group: '财务模块', financeOnly: true },
  { title: '总账记账', path: '/home/ledger', group: '财务模块', financeOnly: true },
  { title: '预算管理', path: '/home/budget', group: '财务模块', financeOnly: true },
  { title: '财务报表', path: '/home/report', group: '财务模块', financeOnly: true },
  { title: '发票上传', path: '/home/invoice-ocr', group: '智能审查' },
  { title: '发票台账', path: '/home/invoice-audit', group: '智能审查' },
  { title: '审查归档', path: '/home/audit-archive', group: '智能审查' },
]

// 按角色显隐（T12e/T16）：带 financeOnly 的菜单仅财务可见
const visibleMenu = computed(() => {
  const role = getUser()?.role
  return menuList.filter(item => !item.financeOnly || role === 'finance')
})

// 按分组归类菜单
const groupedMenu = computed(() => {
  const groups = {}
  visibleMenu.value.forEach(item => {
    if (!groups[item.group]) {
      groups[item.group] = []
    }
    groups[item.group].push(item)
  })
  return groups
})

watch(
  () => route.path,//监听当前页面的URL
  (newPath) => {
    activePath.value = newPath
  },//回调函数
  { immediate: true } // 页面初始化立刻执行
)

const go = (path) => {
  activePath.value = path
  router.push(path)
}

const logout = () => {
  clearSession()
  router.push('/login')
}
</script>

<style scoped>
.layout {
  display: flex;
  height: 100vh;
}
.sidebar {
  width: 220px;
  height: 100vh;
  background: #001529;
  color: white;
  position: fixed;
  left: 0;
  top: 0;
}
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  margin-left: 220px;
}
.header {
  height: 60px;
  background: #fff;
  line-height: 60px;
  padding: 0 20px;
  border-bottom: 1px solid #eee;
}
.content-box {
  flex: 1;
  padding: 20px;
  background: #f5f7fa;
  overflow: auto;
}
.logo {
  padding: 20px;
  font-size: 18px;
  text-align: center;
  background: #002140;
}
.menu-list {
  padding: 10px 0;
}
.menu-group-title {
  padding: 12px 20px 4px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.45);
  text-transform: uppercase;
  letter-spacing: 1px;
}
.menu-item {
  padding: 14px 20px;
  cursor: pointer;
}
.menu-item.active {
  background: #1890ff;
}
.logout {
  position: absolute;
  bottom: 30px;
  width: 100%;
  text-align: center;
  padding: 10px;
  cursor: pointer;
  color: #ff4d4f;
}
</style>