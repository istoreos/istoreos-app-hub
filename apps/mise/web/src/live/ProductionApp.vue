<template>
 <main class="runtime-product">
  <nav class="breadcrumbs" aria-label="面包屑"><span>系统工具</span><span aria-hidden="true">›</span><span>运行时环境</span></nav><div class="workspace-panel"><div class="page-heading"><div><h1 tabindex="-1" ref="heading">运行时环境</h1><p class="subtitle">为每个应用准备合适的版本，让它们各自稳定运行。</p></div><button class="primary" @click="openInstall" :disabled="!writable||busy||!state?.path||!state.online||interrupted">＋ 安装环境</button></div>
  <p v-if="error" class="notice error" role="alert">{{error}} <button class="text-button" @click="refresh()">重新读取</button></p>
  <p v-if="notice" class="notice" role="status">{{notice}} <button class="text-button" aria-label="关闭通知" @click="notice=''">关闭</button></p>
  <section v-if="!state" class="panel empty"><h2>正在读取运行环境</h2><p>请稍候…</p></section>
  <template v-else>
   <p v-if="!writable" class="notice">当前为只读权限，可以查看环境和下载使用入口。</p>
   <p v-for="warning in state.warnings" :key="warning" class="notice warning">{{warning}}</p>
   <section class="device-strip" aria-label="设备与存储摘要"><span><i class="status-dot" :class="{warning:!state.online}"></i>{{state.arch==='x86_64'?'x86_64':'ARM64'}} · 宿主 musl</span><span>{{state.runtimes.length}} 个环境</span><button class="text-button" @click="tab='storage'">{{state.online?(state.free===null?'容量暂不可读':`可用 ${(state.free/1024).toFixed(1)} GiB`):'存储离线'}} <span aria-hidden="true">↗</span></button><span class="accel-status">{{state.acceleration?(state.gateway?'KSpeeder 加速可用':'KSpeeder 不可用'):'使用源站下载'}}</span></section>
   <div v-if="!state.gateway" class="notice warning kspeeder-guide"><div><strong>安装 KSpeeder 可加速下载</strong><p>前往 iStore 安装并启动 KSpeeder，返回后即可选择加速下载；暂不安装也可以使用源站继续。</p></div><a class="guide-link primary" href="/cgi-bin/luci/admin/store">前往 iStore 安装 KSpeeder</a></div>
   <div v-if="!state.path" class="notice"><strong>先为运行环境选择存放位置</strong><p>建议选择开机自动挂载的磁盘。应用数据和环境依赖分别保存。</p><button class="primary" @click="tab='storage'">设置存储位置</button></div>
   <div v-if="state.path&&!state.online" class="notice warning"><strong>运行时目录离线</strong><p>可恢复磁盘挂载，或在存储设置中选择其他仓库。旧目录保留，当前暂停安装与清理。</p></div>
   <div v-if="interrupted" class="notice warning"><strong>有一个中断任务需要处理</strong><p>原有环境保持不变，请先恢复候选，再进行新的操作。</p><button @click="tab='tasks'">查看并恢复</button></div>
   <div v-if="busy" class="running-strip"><span class="spinner" aria-hidden="true"></span><span>{{activeTask?.title}}<small>{{activeTask?.phases[Math.min(activeTask.phase,activeTask.phases.length-1)]}} · 可以离开页面，任务会继续</small></span><button @click="showTask(activeTask!)">查看任务</button></div>
   <nav class="tabs" aria-label="运行时管理"><button v-for="t in tabs" :key="t.id" :aria-current="tab===t.id?'page':undefined" :class="{selected:tab===t.id}" @click="changeTab(t.id)">{{t.title}}<span v-if="t.id==='tasks'&&busy" class="count">1</span></button></nav>
   <section v-if="tab==='runtimes'" class="panel">
    <div class="default-environment"><div><span class="muted">mise 全局默认 · 只读</span><strong>{{defaultLabel(language)}}</strong><small>由 mise 全局配置决定。应用使用自己的固定版本，本页不提供全局切换。</small></div><button v-if="defaultRuntime(language)" @click="usage=defaultRuntime(language)!;copyMessage=''">默认版本使用方法</button></div>
    <div class="section-heading"><div><h2>已安装环境</h2><p>多个版本可以并存，通过专属 wrap 使用具体版本，应用按各自配置运行。</p></div><div class="segmented" aria-label="语言筛选"><button v-for="l in languages" :key="l.id" :class="{selected:language===l.id}" :aria-pressed="language===l.id" @click="language=l.id">{{l.name}}</button></div></div>
    <div v-if="!filtered.length" class="empty"><div class="empty-symbol">＋</div><h3>还没有 {{tools[language].name}} 环境</h3><p>{{state.path?'安装所需版本，再通过专属 wrap 使用。':'设置存储位置后，即可开始安装。'}}</p><button class="primary" @click="state.path?openInstall():tab='storage'" :disabled="!writable||busy||(!!state.path&&!state.online)||interrupted||!state.capabilities[language]?.enabled">{{state.path?'安装环境':'设置存储位置'}}</button></div>
    <div v-else class="runtime-list">
     <article v-for="r in filtered" :key="r.id" class="runtime-row" :data-runtime="r.id"><div class="language-mark" :class="r.language">{{tools[r.language].mark}}</div><div class="runtime-name"><h3>{{tools[r.language].name}} <span>{{versionLabel(r.language,r.version)}}</span></h3><p>{{r.language==='node'?'npm '+r.npm+' · ':''}}{{r.arch}} <span class="badge">{{abiLabel(r.libc)}}</span></p></div><div class="runtime-usage"><p><span :class="{good:r.verified}">{{r.verified?'✓ 已验证':'待验证'}}</span> · {{sizeLabel(r.size)}}</p></div><div class="row-actions"><button @click="usage=r;copyMessage=''">使用此版本</button><button class="text-button" @click="detail=r">详情</button></div></article>
    </div>
    <p class="panel-footnote">{{tools[language].hint}}</p>
   </section>
   <section v-else-if="tab==='tasks'" class="panel">
    <div class="section-heading"><div><h2>任务记录</h2><p>关闭窗口、切换页面或刷新，不会取消正在运行的任务。</p></div></div>
    <div v-if="!state.tasks.length" class="empty"><h3>暂无任务</h3><p>安装和恢复记录会显示在这里。</p></div>
    <article v-for="t in state.tasks" :key="t.id" class="task-row"><div><h3>{{t.title}}</h3><p>{{t.result||t.phases[Math.min(t.phase,t.phases.length-1)]}}</p></div><span class="badge" :class="{good:t.status==='success',bad:t.status==='failed',warning:t.status==='interrupted'}">{{taskLabel[t.status]}}</span><button @click="showTask(t)">查看任务</button></article>
   </section>
   <section v-else class="storage-layout">
    <section class="panel"><div class="section-heading"><div><h2>存储与下载</h2><p>统一保存运行环境，应用仍保留自己的数据目录。</p></div></div><form class="settings-form" @submit.prevent="saveSettings"><label>运行环境存放位置
     <select aria-label="运行环境存放位置" v-model="settingsChoice" :disabled="!writable||state.storageLocked||busy||interrupted" required>
      <option value="" disabled>请选择硬盘目录</option>
      <option v-for="path in storagePaths" :key="path" :value="path">{{path===state.path?'当前目录 · ':''}}{{path}}</option>
      <option value="__custom__">自定义目录…</option>
     </select>
     <small>切换仓库会保留旧目录，不复制环境。空目录需要重新准备依赖；已有仓库可以复用。安装、修复或清理期间不能切换。</small>
    </label>
    <label v-if="settingsCustom">自定义存放目录<input aria-label="自定义存放目录" v-model="settingsPath" placeholder="/mnt/data/Configs/Runtime" :readonly="!writable||state.storageLocked||busy||interrupted" required><small>例如 /mnt/data/Runtime；请选择持久硬盘上的目录。</small></label>
    <p v-if="settingsPath" class="storage-home muted">mise 管理 HOME：<span>{{state.managedHome && settingsPath===state.path ? state.managedHome : settingsPath+'/home'}}</span>。启动脚本会显式设置 HOME。</p>
    <details v-if="storagePaths.some(p=>p!==state?.path)" class="storage-options"><summary>查看其他硬盘目录</summary><ul><li v-for="path in storagePaths.filter(p=>p!==state?.path)" :key="path">{{path}}</li></ul></details><label class="checkbox-label"><input type="checkbox" v-model="settingsAcceleration">通过 KSpeeder 加速下载</label><p class="muted">{{state.gateway?'加速保持源站完整性校验，不改变运行时平台选择。':'KSpeeder 当前不可用。可前往 iStore 安装或启动，也可以关闭加速并使用源站。'}}</p><button class="primary" :disabled="!writable||state.storageLocked||busy||interrupted">保存设置</button></form></section>
    <section class="panel"><div class="section-heading"><div><h2>公共运行库</h2><p>按修订保存，环境固定引用具体的库。</p></div></div><article v-for="lib in state.libraries" :key="lib.id" class="library-row"><div><h3>glibc {{lib.version}} <span class="badge">{{lib.arch}} · {{lib.revision}}</span></h3><p>{{lib.references}} 个环境引用 · {{lib.verified?'安装时验证通过':'运行库缺失或尚未验证'}}</p><small class="mono">{{lib.id}}</small></div><button :disabled="blocked" @click="repairLibrary(lib.id)">检查 / 修复</button><button :disabled="blocked||lib.references>0" @click="confirmAction={kind:'library',id:lib.id,title:'清理闲置运行库',text:`清理 ${lib.id}。后端会再次检查环境引用。`}">清理</button></article><p v-if="!state.libraries.length" class="quiet-empty">尚无私有运行库；安装 glibc 环境时一并准备。</p><button v-if="!state.libraries.length" :disabled="blocked" @click="repairLibrary(state.defaultLibrary)">准备 glibc 2.39</button><p class="muted">修复按固定版本恢复，已安装环境和应用数据保留。修复后请重启相关应用。</p></section>
    <section class="panel"><div class="section-heading"><div><h2>下载缓存</h2><p>缓存用于复用下载，与已安装环境和应用数据分开。</p></div><strong>{{sizeLabel(state.cache)}}</strong></div><div class="panel-actions"><button :disabled="blocked||!state.cache" @click="confirmAction={kind:'cache',title:'清理下载缓存',text:`将释放 ${sizeLabel(state.cache)} 缓存空间，不删除已安装环境或应用数据。`}">清理缓存</button></div></section>
   </section>
  </template>
  <AppDialog v-if="installOpen" :title="plan?'检查安装内容':'安装运行环境'" @close="closeInstall">
   <template v-if="!plan"><p class="dialog-intro">选择一个版本。安装过程不会改变应用现有配置。</p><div class="form-grid"><label>语言<select aria-label="语言" v-model="install.language" @change="resetVersion"><option v-for="l in languages" :key="l.id" :value="l.id" :disabled="!state?.capabilities[l.id]?.enabled">{{tools[l.id].name}}</option></select></label><label>版本<select aria-label="版本" v-model="install.version" @change="resetNpm"><option v-for="v in versions[install.language]" :key="v" :value="v">{{versionLabel(install.language,v)}}</option></select></label><label v-if="tools[install.language].abis.length>1">运行环境<select aria-label="运行环境" v-model="install.libc"><option value="glibc">{{install.language==='rust'?'glibc · 私有宿主运行库':'glibc · 扩展兼容性优先'}}</option><option value="musl">{{install.language==='rust'?'musl · 宿主工具链':'musl · 使用宿主运行库'}}</option></select></label></div><template v-if="install.language==='node'"><p class="hint">默认使用配套 npm {{bundledNpm(install.version)}}；当前选择 {{install.npm}}。</p><details class="npm-advanced" :open="npmAdvanced" @toggle="npmAdvanced=($event.target as HTMLDetailsElement).open"><summary>高级选项 · npm 版本</summary><label v-if="install.language==='node'">npm 版本<select aria-label="npm 版本" v-model="install.npm"><option v-for="v in npmVersions" :key="v" :value="v">{{v}}</option></select></label><p>仅在应用有明确要求时调整，仍需通过兼容性验证。</p></details></template><p v-if="install.language==='python'" class="hint">{{tools.python.hint}}</p><p class="hint">{{['go','rust','zig','java'].includes(install.language)?tools[install.language].hint:install.libc==='glibc'?(install.language==='python'?'适用于需要 glibc 二进制扩展的 Python 应用；应用虚拟环境沿用私有运行库。':'适用于需要 glibc 原生扩展的应用，例如 OpenClaw。私有库与系统隔离。'):'适用于支持 musl 的应用；依赖 glibc 的扩展不能混用。'}}</p><label>下载方式<select aria-label="下载方式" v-model="install.source"><option value="ks-cli" :disabled="!state?.gateway">KSpeeder 加速{{state?.gateway?'':'（服务不可用）'}}</option><option value="origin">源站下载</option></select></label><p v-if="!state?.gateway" class="notice warning">KSpeeder 不可用，可以选择源站继续。</p><p v-if="alreadyInstalled" class="notice">这个环境已经安装，可在环境列表查看详情。</p><p v-if="unsupported" class="notice warning">{{unsupported}}</p></template>
   <template v-else><p class="dialog-intro">核对以下内容后开始。任务在后台运行。</p><ul class="review-list"><li v-for="line in plan.summary" :key="line">{{line}}</li></ul></template>
   <p v-if="dialogError" class="notice error" role="alert">{{dialogError}}</p>
   <template #footer><button @click="plan?plan=null:closeInstall()">{{plan?'上一步':'取消'}}</button><button class="primary" :disabled="working||alreadyInstalled||!!unsupported" @click="plan?submit():reviewInstall()">{{working?'正在处理…':plan?'开始安装':'检查安装内容'}}</button></template>
  </AppDialog>
  <AppDialog v-if="detail" :title="`${tools[detail.language].name} ${versionLabel(detail.language,detail.version)}`" @close="detail=null">
   <dl class="detail-grid"><dt>运行环境</dt><dd>{{detail.arch}} · {{abiLabel(detail.libc)}}</dd><template v-if="detail.npm"><dt>npm</dt><dd>{{detail.npm}}</dd></template><template v-if="detail.language==='java'"><dt>发行版</dt><dd>Eclipse Temurin · 完整 JDK · LTS</dd></template><template v-if="detail.language==='python'"><dt>配套 pip</dt><dd>{{detail.pythonTools?.pipVersion||'尚未读取版本'}}</dd><dt>venv 状态</dt><dd>{{detail.pythonTools?.venv==='passed'?'可用 · 创建与 pip 初始化检查通过':detail.pythonTools?.venv==='failed'?'验证失败':'尚未验证'}}</dd></template><dt>验证状态</dt><dd :class="{good:detail.verified}">{{detail.verified?'✓ 安装验证通过':'尚未完成全部验证'}}</dd><template v-if="detail.language==='rust'"><dt>宿主工具链</dt><dd>{{rustHost(detail.arch,detail.libc)}} · minimal</dd></template><dt>全局默认</dt><dd>{{isDefault(state!,detail.id)?'是 · 本页不提供切换':'否'}}</dd><dt>占用空间</dt><dd>{{sizeLabel(detail.size)}}</dd></dl><details><summary>查看技术信息</summary><p class="mono">{{state?.path}}/environments/{{detail.id}}</p><p>检查结果：{{probeLabel(detail)}}</p></details>
   <template #footer><button @click="detail=null">完成</button><button class="danger" :disabled="isDefault(state!,detail.id)||!state?.defaultsKnown[detail.language]||blocked" @click="confirmAction={kind:'runtime',id:detail.id,title:'清理环境',text:`删除 ${detail.language} ${versionLabel(detail.language,detail.version)} · ${abiLabel(detail.libc)}，释放 ${sizeLabel(detail.size)}。应用数据和下载缓存保留。固定 wrap 入口将失效，依赖它的应用或脚本将无法启动。请自行确认使用情况。`};detail=null">清理环境</button></template>
  </AppDialog>
  <AppDialog v-if="usage" :title="`使用 ${tools[usage.language].name} ${versionLabel(usage.language,usage.version)} · ${abiLabel(usage.libc)}`" @close="usage=null">
   <p class="dialog-intro">通过固定版本 wrap 启动，自动设置硬盘上的 HOME、缓存和 mise 目录；无需修改 /root 或全局默认版本。</p>
   <div class="usage-commands"><label v-for="(line,i) in usageCommands(state!.path,usage)" :key="line">{{tools[usage.language].usageLabels[i]||'进入该版本环境'}}<div class="copy-line"><input :aria-label="`使用命令 ${i+1}`" :value="line" readonly><button @click="copy(line)">复制</button></div></label></div>
   <section v-if="usage.language==='python'" class="python-project"><h3>应用虚拟环境</h3><p>为每个应用创建独立环境，再安装依赖。下列为命令示例，网页不会创建目录或安装包。</p><label>虚拟环境目录<input aria-label="虚拟环境目录" v-model="projectPath" placeholder="/mnt/data/my-app/.venv"><small>请选择当前用户拥有的持久分区新目录；已有目录不会覆盖。requirements.txt 和 app.py 按你的项目替换。</small></label><p v-if="projectPathError" class="notice warning" role="alert">{{projectPathError}}</p><div v-else class="usage-commands"><label v-for="(line,i) in projectCommands" :key="line">{{['创建虚拟环境（含 pip）','安装应用依赖','运行应用','进入虚拟环境'][i]}}<div class="copy-line"><input :aria-label="`虚拟环境命令 ${i+1}`" :value="line" readonly><button @click="copy(line)">复制</button></div></label></div><p class="hint">共享 pip 入口仅用于查询版本。指定虚拟环境后，pip、Python 和子进程沿用该固定运行时；外来、归属不匹配或未验证的虚拟环境会明确报错。需要特殊 pip 版本时，在应用自己的环境中升级。</p></section>
   <p class="hint">root 默认 HOME：{{state!.path}}/home；其他用户：{{state!.path}}/users/&lt;用户 ID&gt;/home。wrap 会显式设置 HOME；应用可用 ISTORE_RUNTIME_HOME 指向自己的持久数据目录。</p>
   <p v-if="['go','rust','zig','java'].includes(usage.language)" class="hint">{{tools[usage.language].hint}}<template v-if="usage.language==='go'"> 固定 GOTOOLCHAIN=local，不会自动下载其他版本。</template><template v-if="usage.language==='rust'"> 固定调用此工具链的 rustc/cargo；不提供 rustup 管理入口。</template></p><details><summary>wrap 脚本与目录约定</summary><p>正式安装时随环境生成入口。以下脚本来自所选实例的实际入口。</p><pre>{{wrapText||'正在读取实际入口…'}}</pre><p>glibc 环境调用该环境的私有 loader 启动入口，不向系统命令设置全局 LD_LIBRARY_PATH。</p></details>
   <p v-if="copyMessage" role="status" class="copy-result">{{copyMessage}}</p>
   <template #footer><button @click="usage=null">完成</button><button @click="downloadWrap">下载 wrap 脚本</button></template>
  </AppDialog>
  <AppDialog v-if="taskDetail" :title="taskDetail.title" @close="taskId=''">
   <div class="task-result" :class="{bad:taskDetail.status==='failed'}"><span class="badge">{{taskLabel[taskDetail.status]}}</span><p>{{taskDetail.result||'任务进行中，关闭窗口后仍会继续。'}}</p></div><ol class="phase-list"><li v-for="(p,i) in taskDetail.phases" :key="p" :class="{done:i<taskDetail.phase&&i!==taskDetail.failedPhase,bad:i===taskDetail.failedPhase,active:i===taskDetail.phase&&taskDetail.status==='running'}"><span>{{i===taskDetail.failedPhase?'×':i<taskDetail.phase?'✓':i+1}}</span>{{p}}</li></ol><details><summary>查看详细日志</summary><pre>{{taskDetail.logs.join('\n')}}</pre></details><p v-if="dialogError" class="notice error" role="alert">{{dialogError}}</p>
   <template #footer><button @click="taskId=''">{{taskDetail.status==='running'?'后台继续':'关闭'}}</button><button v-if="taskDetail.status==='running'" class="danger" @click="taskAction('cancel')" :disabled="working||!writable">取消任务</button><button v-if="taskDetail.status==='interrupted'" class="primary" @click="taskAction('recover')" :disabled="working||!writable">恢复并清理候选</button><button v-if="['failed','canceled'].includes(taskDetail.status)" :disabled="blocked" @click="retryTask(taskDetail)">重新检查</button><button v-if="taskDetail.status==='success'" class="primary" @click="showInstalled(taskDetail)">查看使用方法</button></template>
  </AppDialog>
  <AppDialog v-if="switchOpen" title="切换运行时仓库" @close="switchOpen=false">
   <p>将从 {{state?.path||'未配置'}} 切换到 {{settingsPath}}。</p><p>旧目录及其内容完整保留，不会复制到新目录。空目录将从零准备环境；已有仓库则复用原有内容。</p><p>请手动重启相关应用，或重启系统。应用会按自身规则准备固定版本；首次准备可能需要联网下载。手写的旧绝对路径脚本仍指向旧仓库，需要自行调整。</p><p>默认 HOME 随仓库切换，旧 HOME 中的工具登录和配置不会复制，可能需要重新登录。明确设置的兼容 HOME 保持原位置。</p><p v-if="dialogError" class="notice error" role="alert">{{dialogError}}</p>
   <template #footer><button @click="switchOpen=false">取消</button><button class="primary" :disabled="working||busy||interrupted||!writable" @click="persistSettings">确认切换</button></template>
  </AppDialog>
  <AppDialog v-if="confirmAction" :title="confirmAction.title" @close="confirmAction=null"><p>{{confirmAction.text}}</p><p v-if="dialogError" class="notice error" role="alert">{{dialogError}}</p><template #footer><button @click="confirmAction=null">取消</button><button class="danger" :disabled="working||!writable" @click="executeCleanup">确认清理</button></template></AppDialog>
 </div></main>
</template>
<script setup lang="ts">
import {computed,onMounted,onUnmounted,ref,watch} from 'vue'
import AppDialog from '../components/AppDialog.vue'
import {tools,languages,abiLabel,rustHost,versionLabel} from './labels'
import {isDefault,usageCommands,pythonProjectCommands,venvPathError,sizeLabel,type State,type Runtime,type Task,type Plan,type Language,type Libc} from './model'
import type {LiveService} from './service'
const props=defineProps<{service:LiveService}>(),writable=props.service.writable
const state=ref<State>(),tab=ref('runtimes'),language=ref<Language>('node'),error=ref(''),notice=ref(''),working=ref(false),dialogError=ref(''),heading=ref<HTMLElement>()
const tabs=[{id:'runtimes',title:'运行环境'},{id:'tasks',title:'任务记录'},{id:'storage',title:'存储与设置'}]
const activeTask=computed(()=>state.value?.tasks.find(t=>t.status==='running')),busy=computed(()=>!!activeTask.value),interrupted=computed(()=>!!state.value?.tasks.some(t=>t.status==='interrupted')),blocked=computed(()=>!writable||busy.value||interrupted.value||state.value?.storageLocked||!state.value?.online||!state.value?.path)
const filtered=computed(()=>state.value?.runtimes.filter(r=>r.language===language.value)||[])
const detail=ref<Runtime|null>(null),installOpen=ref(false),plan=ref<Plan|null>(null),usage=ref<Runtime|null>(null),copyMessage=ref(''),taskId=ref(''),taskDetail=computed(()=>state.value?.tasks.find(t=>t.id===taskId.value)),settingsPath=ref(''),settingsAcceleration=ref(true),wrapText=ref('')
const projectPath=ref(''),npmAdvanced=ref(false),settingsCustom=ref(false),switchOpen=ref(false)
const storagePaths=computed(()=>[...new Set([state.value?.path,...(state.value?.storagePaths||[])].filter((p):p is string=>!!p))])
const settingsChoice=computed({get:()=>settingsCustom.value?'__custom__':settingsPath.value,set:(path:string)=>{settingsCustom.value=path==='__custom__';if(!settingsCustom.value)settingsPath.value=path}})
function resetSettings(s:State){settingsPath.value=s.path||s.storageDefault;settingsAcceleration.value=s.acceleration;settingsCustom.value=!settingsPath.value&&!s.storagePaths.length}

const projectPathError=computed(()=>state.value?venvPathError(state.value.path,projectPath.value):'')
const projectCommands=computed(()=>usage.value&&state.value?pythonProjectCommands(state.value.path,usage.value,projectPath.value):[])
watch(usage,async r=>{
 wrapText.value='';copyMessage.value=''
 if(!r||!state.value)return
 if(r.language==='python')projectPath.value=state.value.path+'/projects/my-app/'+r.id+'/.venv'
 try{const text=await props.service.wrap(r.id);if(usage.value?.id===r.id)wrapText.value=text}catch(e){copyMessage.value=(e as Error).message}
})
const versions=computed(()=>Object.fromEntries(languages.map(({id})=>[id,[...new Set(state.value?.catalog.filter(e=>e.tool===id&&e.availability==='available').map(e=>e.version)||[])].sort((a,b)=>b.localeCompare(a,undefined,{numeric:true}))]))as Record<Language,string[]>)
const install=ref({language:'node'as Language,version:'',libc:'glibc'as Libc,npm:'',source:'origin'as'origin'|'ks-cli'})
const entries=computed(()=>state.value?.catalog.filter(e=>e.tool===install.value.language&&e.version===install.value.version&&e.abi===install.value.libc&&e.availability==='available')||[])
function bundledNpm(version:string){return state.value?.catalog.find(e=>e.tool==='node'&&e.version===version&&e.abi===install.value.libc&&e.artifacts.length===1)?.npm||''}
const npmVersions=computed(()=>{const values=[...new Set(entries.value.map(e=>e.npm).filter((x):x is string=>!!x))],bundled=bundledNpm(install.value.version);return values.sort((a,b)=>a===bundled?-1:b===bundled?1:b.localeCompare(a,undefined,{numeric:true}))})
const selectedEntry=computed(()=>entries.value.find(e=>e.tool!=='node'||e.npm===install.value.npm))
const alreadyInstalled=computed(()=>!!selectedEntry.value&&state.value?.runtimes.some(r=>r.entryId===selectedEntry.value!.id&&(r.libc!=='glibc'||r.library===state.value?.defaultLibrary)))
const unsupported=computed(()=>!state.value?.capabilities[install.value.language]?.enabled?(state.value?.capabilities[install.value.language]?.reason||'当前语言尚未启用'):!selectedEntry.value?'目录没有提供此版本、架构、运行库或 npm 组合。':'')
const confirmAction=ref<{kind:string;id?:string;title:string;text:string}|null>(null)
const taskLabel={running:'进行中',success:'已完成',failed:'失败',canceled:'已取消',interrupted:'需要恢复'}
function apply(s:State,settings=false){if(state.value&&s.stamp<state.value.stamp)return;state.value=s;if(settings)resetSettings(s)}
async function refresh(settings=false){try{apply(await props.service.read(),settings||!state.value);error.value=''}catch(e){error.value=(e as Error).message}}
function changeTab(id:string){tab.value=id;notice.value='';if(id==='storage'&&state.value)resetSettings(state.value)}
function openInstall(){npmAdvanced.value=false;dialogError.value='';notice.value='';plan.value=null;install.value={language:language.value,version:versions.value[language.value][0]||'',libc:tools[language.value].defaultAbi,npm:'',source:state.value?.acceleration&&state.value.gateway?'ks-cli':'origin'};resetNpm();installOpen.value=true}
function closeInstall(){installOpen.value=false;plan.value=null;dialogError.value=''}
function resetVersion(){npmAdvanced.value=false;install.value.version=versions.value[install.value.language][0]||'';install.value.libc=tools[install.value.language].defaultAbi;resetNpm()}
function resetNpm(){install.value.npm=install.value.language==='node'?bundledNpm(install.value.version):''}
async function reviewInstall(){working.value=true;dialogError.value='';try{if(!selectedEntry.value)throw Error('请选择目录提供的版本');plan.value=await props.service.plan(selectedEntry.value,install.value.source)}catch(e){dialogError.value=(e as Error).message}finally{working.value=false}}
async function submit(){working.value=true;try{const task=await props.service.act('submit',plan.value!.id);await refresh();installOpen.value=false;plan.value=null;tab.value='tasks';taskId.value=task.id||''}catch(e){dialogError.value=(e as Error).message;plan.value=null}finally{working.value=false}}
function showTask(t:Task){taskId.value=t.id;dialogError.value=''}
async function taskAction(action:'cancel'|'recover'){working.value=true;try{await props.service.act(action,taskId.value);await refresh()}catch(e){dialogError.value=(e as Error).message}finally{working.value=false}}
function retryTask(t:Task){taskId.value='';if(t.library){void repairLibrary(t.library);return}openInstall();if(t.runtime){install.value.language=t.runtime.language;install.value.version=t.runtime.version;install.value.libc=t.runtime.libc;install.value.npm=t.runtime.npm}}
function defaultRuntime(l:Language){return state.value?.runtimes.find(r=>r.id===state.value!.defaults[l])||null}
function defaultLabel(l:Language){return state.value?.defaultLabels[l]||'尚未读取默认版本'}
function showInstalled(t:Task){taskId.value='';tab.value='runtimes';const r=state.value?.runtimes.find(r=>r.id===t.runtime?.id);if(r){language.value=r.language;usage.value=r;copyMessage.value=''}else notice.value='对应环境尚未读取或已经清理。'}
function probeLabel(r:Runtime){return Object.entries(r.probes).map(([name,result])=>`${name}: ${result}`).join(' · ')}
async function copy(text:string){try{if(navigator.clipboard&&window.isSecureContext)await navigator.clipboard.writeText(text);else{const input=document.createElement('textarea');input.value=text;document.querySelector('dialog')!.append(input);input.select();const ok=document.execCommand('copy');input.remove();if(!ok)throw Error('unavailable')}copyMessage.value='命令已复制。'}catch{copyMessage.value='浏览器未允许复制，请选中命令后手动复制。'}}
async function downloadWrap(){const r=usage.value;if(!r)return;try{const text=await props.service.wrap(r.id),url=URL.createObjectURL(new Blob([text],{type:'text/x-shellscript'})),a=document.createElement('a');a.href=url;a.download=r.id+'.sh';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);copyMessage.value='已下载此实例的实际 wrap 脚本。'}catch(e){copyMessage.value=(e as Error).message}}
async function executeCleanup(){working.value=true;try{const c=confirmAction.value!;await props.service.act(c.kind==='runtime'?'remove':c.kind==='library'?'library-remove':'cache-clear',c.id);await refresh();confirmAction.value=null;notice.value='清理完成，应用数据保持不变。'}catch(e){dialogError.value=(e as Error).message}finally{working.value=false}}
async function saveSettings(){dialogError.value='';if(settingsPath.value!==state.value?.path){switchOpen.value=true;return}await persistSettings()}
async function persistSettings(){working.value=true;const changed=settingsPath.value!==state.value?.path;try{await props.service.settings(settingsPath.value,settingsAcceleration.value);await refresh(true);switchOpen.value=false;notice.value=changed?'仓库已切换，旧目录完整保留。请重启相关应用或系统；新仓库的依赖将由应用按需准备，工具可能需要重新登录。':'设置已保存。';error.value=''}catch(e){if(switchOpen.value)dialogError.value=(e as Error).message;else error.value=(e as Error).message}finally{working.value=false}}
async function repairLibrary(id:string){working.value=true;try{const result=await props.service.repairLibrary(id,state.value?.acceleration?'ks-cli':'origin');await refresh();tab.value='tasks';taskId.value=result.task.id;notice.value='已提交运行库检查 / 修复。完成后请重启相关应用。'}catch(e){error.value=(e as Error).message}finally{working.value=false}}
let timer:ReturnType<typeof setTimeout>|undefined,alive=true
async function poll(){if(!document.hidden)await refresh();if(alive)timer=setTimeout(poll,busy.value?1200:5000)}
onMounted(()=>{void poll()});onUnmounted(()=>{alive=false;clearTimeout(timer)})
</script>
<style scoped src="../styles/quickstart/workspace.css"></style>
