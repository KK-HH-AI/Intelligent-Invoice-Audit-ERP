<template>
  <div class="register-container">
    <div class="register-box">
      <form>
        <h2 v-once>ERP 财务系统 - 注册</h2>
        <div class="form-item">
          <label>账号</label>
          <input v-model="form.username" type="text" placeholder="设置账号" />
        </div>
        <div class="form-item">
          <label>密码</label>
          <input v-model="form.password" type="password" placeholder="设置密码" />
        </div>
        <button class="btn register" @click="register">注册</button>
      </form>

      <div class="link" @click="$router.push('/login')">
        已有账号？立即登录
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const form = reactive({ username: '', password: '' })

const register = () => {
  const { username, password } = form
  if (!username || !password) {
    alert('请完善信息')
    return
  }
  localStorage.setItem(
    'erp-user',
    JSON.stringify({ name: username, pwd: password })
  )//持久化
  alert('注册成功！请登录')
  router.push('/login')
}
</script>

<style scoped>
.register-container {
  width: 100vw;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #e8f0fe;
}
.register-box {
  width: 400px;
  padding: 40px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 0 20px #0001;
}
.form-item {
  margin: 20px 0;
}
input {
  width: 100%;
  padding: 10px;
  margin-top: 6px;
  border: 1px solid #ddd;
  border-radius: 6px;
}
.btn {
  width: 100%;
  padding: 12px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}
.register {
  background: #67c23a;
  color: white;
}
.link {
  text-align: center;
  margin-top: 16px;
  color: #409eff;
  cursor: pointer;
}
</style>