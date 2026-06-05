import { defineStore } from 'pinia'
import { ref } from 'vue'

//暴露财务全局数据
export const useFinanceStore = defineStore('finance', () => {
 // 报销单数据
 const reimburseList = ref([])

 // 应收单数据
 const receivableList = ref([])
 
 // 应付单数据
 const payableList = ref([])

 // 凭证数据
 const voucherList = ref([])

 // 总账科目余额
 const ledgerAccounts = ref([
  { code: '1002', name: '银行存款', opening: 100000, debit: 0, credit: 0, closing: 100000 },
  { code: '1122', name: '应收账款', opening: 0, debit: 0, credit: 0, closing: 0 },
  { code: '2202', name: '应付账款', opening: 0, debit: 0, credit: 0, closing: 0 },
  { code: '6001', name: '主营业务收入', opening: 0, debit: 0, credit: 0, closing: 0 },
  { code: '6401', name: '主营业务成本', opening: 0, debit: 0, credit: 0, closing: 0 },
  { code: '6602', name: '管理费用', opening: 0, debit: 0, credit: 0, closing: 0 },
 ])

 return {
  reimburseList,
  receivableList,
  payableList,
  voucherList,
  ledgerAccounts,
 }
})