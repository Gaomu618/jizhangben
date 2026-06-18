// 测试入口
const { summary } = require('./runner')

console.log('\x1b[1m\x1b[35m🧪 UI 改进测试套件\x1b[0m')
console.log('\x1b[2m测试 #3 微动效 + #4 空状态/加载/错误 + #5 页面切换动效\x1b[0m')

require('./motion.test')
require('./empty-state.test')
require('./navigation.test')
require('./chart-tooltip.test')
require('./profile-api.test')

const failed = summary()

if (failed > 0) {
  console.log('\n\x1b[31m❌ 测试未通过，需要实施代码\x1b[0m')
  process.exit(1)
} else {
  console.log('\n\x1b[32m✅ 全部测试通过\x1b[0m')
  process.exit(0)
}