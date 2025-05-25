 document.getElementById('downloadBtn').addEventListener('click', function() {
        console.log('按钮被点击了');
        // 保存原始背景色
  const originalColor = this.style.backgroundColor;
  
  // 修改按钮样式（点击时）
  this.style.backgroundColor = '#0F4CDD'; // 深一点的蓝色
  // 目标：截图包含水质数据的容器（假设外层容器 class 为 data-container）
  const targetElement = document.querySelector('.chart'); // 根据实际结构调整选择器

  html2canvas(targetElement, {
    useCORS: true, // 允许跨域（若图片涉及外部资源）
    logging: false, // 关闭控制台日志
    backgroundColor: null, // 背景透明（若需要）
  }).then(canvas => {
    // 将 canvas 转为图片 URL
    const imgURL = canvas.toDataURL('image/png');
    
    // 创建下载链接
    const link = document.createElement('a');
    link.href = imgURL;
    link.download = `水质数据展示_${new Date().toISOString().replace(/:/g, '-')}.png`; // 文件名含时间戳
    setTimeout(() => {
      this.style.backgroundColor = originalColor;
    }, 300); // 300ms 后恢复
    // 触发下载
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  });
});