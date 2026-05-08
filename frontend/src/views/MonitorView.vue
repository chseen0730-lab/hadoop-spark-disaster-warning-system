<template>
  <section class="view-wrap">
    <header class="view-header">
      <h2>系统监控</h2>
      <p>直接查看 Spark UI 与 Hadoop NameNode 运行状态</p>
    </header>
    <div class="monitor-actions">
      <a class="monitor-link" href="http://localhost:8080" target="_blank" rel="noreferrer">打开 Spark 原生 UI</a>
      <a class="monitor-link" href="http://localhost:9870" target="_blank" rel="noreferrer">打开 NameNode 原生 UI</a>
    </div>
    <div class="monitor-grid">
      <article class="glass-card monitor-card">
        <h3>Spark Master UI</h3>
        <iframe src="http://localhost:8000/api/proxy/spark/" title="Spark UI" />
      </article>
      <article class="glass-card monitor-card">
        <h3>Hadoop NameNode UI</h3>
        <iframe src="http://localhost:8000/api/proxy/hdfs/" title="Hadoop NameNode UI" />
      </article>
    </div>
  </section>
</template>
