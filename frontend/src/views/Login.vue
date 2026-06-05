<template>
  <div class="login-container"><!--使得登录界面居中--->
    <div class="login-box">
      <h2>ERP 财务系统登录</h2>
      
      <form  @submit.prevent="login"><!--用prevent阻止页面刷新，防止当前的状态等全部清零-->
        <div class="form-item">
          <label>账号</label>
          <input v-model="form.username" type="text" placeholder="请输入账号" />
        </div>

        <div class="form-item">
          <label>密码</label>
          <input v-model="form.password" type="password" placeholder="请输入密码" />
        </div>

        <div class="btn-group">
          <button class="login-btn" @click="login">登录</button>
          <button class="register-btn" @click="goRegister">去注册</button>
        </div>
      </form>
      
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()//用于在组件内使用路由跳转
const form = ref({
  username: '',
  password: ''
})

// 登录逻辑
const login = () => {
  const { username, password } = form.value
  
  if (!username || !password) {
    alert('请输入账号和密码')
    return
  }

  const user = localStorage.getItem('erp-user')
  if (!user) {
    alert('未注册，请先注册')
    return
  }

  const { name, pwd } = JSON.parse(user)
  if (name === username && pwd === password) {
    router.push('/home/receivable')
  } else {
    alert('账号或密码错误')
  }
}

// 去注册页
const goRegister = () => {
  router.push('/register')
}
</script>

<style scoped>
.login-container {
  width: 100vw;
  height: 100vh;
  background: #f5f7fa;
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-box {
  width: 400px;
  background: white;
  padding: 40px;
  border-radius: 8px;
  box-shadow: 0 0 12px rgba(0, 0, 0, 0.1);
}

.login-box h2 {
  text-align: center;
  margin-bottom: 30px;
  color: #333;
}

.form-item {
  margin-bottom: 20px;
}

.form-item label {
  display: block;
  margin-bottom: 8px;
  color: #666;
}

.form-item input {
  width: 100%;
  height: 40px;
  padding: 0 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  box-sizing: border-box;
}

.btn-group {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}

.login-btn {
  flex: 1;
  height: 42px;
  background: #409eff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.register-btn {
  flex: 1;
  height: 42px;
  background: #6c757d;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
</style>