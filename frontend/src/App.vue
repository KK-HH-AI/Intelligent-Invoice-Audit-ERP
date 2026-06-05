<template>
  <div id="app">
    <router-view /> <!-- 路由占位，匹配到那个路由，这里就渲染哪个路由-->
  </div>
</template>

<script setup>
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
  font-family: Arial, sans-serif;
}
body {
  background: #f5f7fa;
}
</style>