'use strict';

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
const versions = window.VERSIONS;
const slides = $$('.slide');
const starter = '请根据我的资料，为我制作一条视频：在你的视角里，我是一个什么样的人。\n\n资料在：【聊天记录路径】【笔记路径】【项目文件夹】【头像路径】\n\n用真实数据和原话，引用标日期并核对。统计活跃时间只使用时间字段；引用原话时另行核对原文。时长、画面、声音和技术方案由你决定。\n\n先给我看几张关键帧，确认方向后再渲染整片。';
const notes = [
  ['0:00–0:35 · 开场', '今天分享的是一次真实创作：我让 Opus 5.5 根据自己的资料做个人短片，后来迭代出 12 版。大家可以带走制作思路和提示词。不需要从技术细节讲起，先把故事和作品给大家看。', '素材：项目公众号文章、12 版本地成片。模型名称沿用本次分享主题。'],
  ['0:35–1:20 · 交代动机', '五个月里，聊天与项目留下了很多痕迹。我好奇 AI 会怎样理解这些痕迹，于是问：在你眼里，我是什么样的人？这里的 147 天、1,319 条消息和 12 个项目来自已有创作记录，12 个项目与 12 个视频版本是两个不同概念。', '来源：公众号文章《我让 AI 给我拍了 12 支短片》开头；未重新统计原始聊天记录。'],
  ['1:20–2:50 · 播放作品', '建议先播放 V11 快闪，再切换 V10 江城、V8 冒险，各播一个片段。让大家注意：故事素材相同，但节奏、声音和视觉语言完全不同。这里可以打开任意版本的截图和完整提示词。片段都在本地，无需联网。', '片段直接截自 out 中的原始 MP4；界面显示原片时长和截取位置。'],
  ['2:50–3:40 · 讲清制作方式', '这是让 Claude Code 读取资料、写动画代码并调用工具渲染视频的项目实践。人的工作贯穿其中：提供资料，判断故事，选择样片，给出修改意见。可以把整条链路理解为“资料—叙事—样片—成片”。', '来源：文章“开始之前”和各版提示词；只描述本项目流程，不作模型能力或效果保证。'],
  ['3:40–4:30 · 准备内容', '最重要的素材是有日期的原话和实际做过的事。给一张头像，主角就有了视觉锚点。统计时间和引用原话分开处理：统计只用时间字段，引用再核对相应文本。共享前选好能公开的内容。', '来源：文章“开始之前”、V1 与 V9 提示词。'],
  ['4:30–5:30 · 拆起步提示词', '这一页是为分享压缩的起步模板，不是声称最初完整对话逐字如此。明确主题、提供资料、要求真实、设置样片检查点即可。技术和部分创意可以留给 AI。点击可复制；详细版在作品放映室。', '来源：V1 提示词与文章经验；本页为改写后的分享版。'],
  ['5:30–6:20 · 说明迭代逻辑', '第一版先把故事成立起来。第二到第四版围绕声音做尝试。第五版保留内容和声音重做画面，第六版连配乐与节奏都重新处理，后面的版本探索不同风格。每轮都说清楚保留什么、改变什么。', '来源：文章 V1–V12 版本说明。'],
  ['6:20–7:20 · 听声音', '可以播放一段女声，再选男声或双声，让大家听叙述者的变化。配音最实用的经验是：逐句合成、转写回来、与原稿比对，读错哪句重做哪句。片段是各版本的示例，不是严格逐句对齐的音色实验。', '来源：V2–V4 提示词。V1 片段起点 00:45；V2–V4 起点 01:18。'],
  ['7:20–8:35 · 讲风格规则', '请大家任选一个风格。字版把每个画面都做成字；RPG 把经历变成游戏机制；水墨把项目化成江上的千帆。这些约束同时影响画面、叙事和声音。点开任意一张，可以看到完整原始提示词。', '来源：V7–V12 提示词与成片截图。'],
  ['8:35–9:20 · 降低试错成本', '水墨版确定方向之前，先看过同一场景的扁平插画、纸雕书、水墨和全息科幻样片。这里用的是项目里保存的原图。先把风格选择做小，再进入整片制作，可以更早发现方向不合适。', '来源：文章 V10 后的小技巧；build/v10-samples/V10-四种风格样片.jpg。'],
  ['9:20–10:15 · 把感受说具体', '150 BPM 代表每拍 0.4 秒，30 帧每秒就是每拍 12 帧；八分音符是 0.2 秒。这种可执行的节奏要求，让文字变化、音乐重拍和镜头动作有共同的时间标尺。播放快闪片段即可感受。', '来源：V11 提示词；计算：60 ÷ 150 × 30 = 12 帧。'],
  ['10:15–11:25 · 反馈演示', '文章里“效果还是差一些”这样的直觉反馈就能推进工作。分享时再补充具体段落与验收方向，会更容易判断下一版。这里三组例子分别对应节奏、可读性和配音问题；右侧是根据原文整理的可执行反馈。', '来源：文章“做的过程中，这几句话很好用”；右侧反馈为分享改写。'],
  ['11:25–13:00 · 现场操作', '请一位听众选风格。我填入素材路径，现场生成并复制一条起步提示词。这里是离线文字模板，不会读取文件，也不会调用模型。复制后到 Claude Code 使用，按自己的项目情况调整即可。', '来源：本项目通用要求和各风格提示词的精简组合。'],
  ['13:00–14:05 · 行动建议', '不需要一开始就做 12 版。先挑一个主题，整理一份素材，做几张关键帧；如果要验证节奏，再出一段 15 秒样片。判断像不像自己、是否清楚、是否动人，然后再做下一轮。', '依据：文章“几点经验”；此页为分享行动建议。'],
  ['14:05–15:00 · 收尾与交流', '最后用片子里的这句回答收尾，然后把问题交给大家：你想让 AI 替你讲一个什么故事？如果大家想继续看，可以回到放映室；完整视频和项目资料链接在右侧。外部链接需要联网。', '引文来源：文章结尾；B 站与 GitHub 链接来自项目资料。']
];
const feedback = [
  {label:'冲击不够', quote:'“效果还是差一些，\n给我的感觉还是不够。”', action:'挑一段高潮，重做 15 秒样片。', explain:'明确拉开快慢与强弱，检查节奏是否太松、音乐是否太薄；让关键动作落在重拍上。', copy:'这段高潮的冲击还不够。先重做一段 15 秒样片：检查节奏、画面密度、空间感和音乐层次，拉开快慢与强弱，让关键动作落在重拍上。说明你改了什么，我确认后再做整片。'},
  {label:'画面看不清', quote:'“这一段画面\n很难分辨出来。”', action:'先让观众一眼看懂主角与信息。', explain:'指出具体段落，减少同时出现的元素，突出关键数字或文字，再给一张修改前后的关键帧。', copy:'这一段画面很难分辨出来。请先让观众一眼看懂这张图在说什么，减少同时出现的元素，突出关键数字或文字。给我修改前后的关键帧对比，确认后再渲染。'},
  {label:'配音读错', quote:'“把每句配音转写回来，\n和原稿逐字比对。”', action:'定位到句，只重做未通过的部分。', explain:'重点检查多音字、英文与人名；保留已经正确的句子，不为了读顺而改掉原话的意思。', copy:'把每句配音转写回来和原稿逐字比对，重点检查多音字、英文和人名。只重做没通过的句子，已通过的不要动；不要改掉我的原话。'}
];
const styles = [
  {id:7,label:'字',rule:'画面只由字组成；黑白与印章红。',prompt:'整部片子只由字组成，数字、地图、头像都用字拼出来。配色只有黑、白与印章红，配乐采用极简电子。'},
  {id:8,label:'像素冒险',rule:'经历变关卡，项目变任务奖励。',prompt:'把经历讲成一场像素 RPG：消息是经验值，项目是任务奖励，习惯是技能树。画面与音乐统一为像素游戏和 8-bit 风格。'},
  {id:9,label:'手账书信',rule:'原话贴在纸上，声音像在读信。',prompt:'把故事写成一封手写信，放进点阵手账。原话写在便利贴上，头像从铅笔素描晕成水彩，加入翻页与纸笔声音。'},
  {id:10,label:'水墨江城',rule:'长卷、留白，经历化成城市风物。',prompt:'用一幅水墨长卷一镜到底，经历对应我的城市风物。以墨色、朱砂和少量赭黄统一画面，配古琴与箫，不用人声。'},
  {id:11,label:'快闪',rule:'150 BPM，点线面体随节拍变化。',prompt:'做一支纯音乐快闪短片，150 BPM，点、线、面、体连续变换。黑白红配色，让文字、镜头与音乐重拍对齐。'},
  {id:12,label:'黑白漫画',rule:'镜头逐格读，拟声字也有声音。',prompt:'把故事做成黑白网点漫画，镜头逐格阅读，读完翻页。AI 的话在旁白框，我的原话在气泡里；拟声字配对应音效。'}
];
let current = 0;
let selectedVersion = 11;
let selectedFeedback = 0;
let selectedStyle = styles[3];
let detailVersion = versions[0];
let toastTimer;

function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}

function toast(message) {
  const node = $('#toast');
  clearTimeout(toastTimer);
  node.textContent = message;
  node.hidden = false;
  toastTimer = setTimeout(() => { node.hidden = true; }, 3200);
}

async function copyText(text) {
  try {
    if (!navigator.clipboard?.writeText) throw new Error('Clipboard API unavailable');
    await navigator.clipboard.writeText(text);
    toast('提示词已复制');
  } catch {
    const textarea = element('textarea');
    textarea.value = text;
    textarea.style.cssText = 'position:fixed;left:0;top:0;opacity:0;';
    const parent = $('dialog[open]') || document.body;
    const previous = document.activeElement;
    parent.append(textarea);
    textarea.select();
    let copied = false;
    try { copied = document.execCommand('copy'); } catch { /* Offer a manual copy field below. */ }
    textarea.remove();
    previous?.focus({preventScroll:true});
    if (copied) { toast('提示词已复制'); return; }
    const dialog = element('dialog');
    const heading = element('h2', '请手动复制提示词');
    const help = element('p', '浏览器未允许自动复制。下方文字已选中，按 ⌘C / Ctrl+C 复制。');
    const field = element('textarea');
    field.value = text;
    field.setAttribute('aria-label','手动复制提示词');
    field.style.cssText='width:100%;height:45vh;margin:20px 0;padding:20px;font:inherit;line-height:1.7;';
    const close = element('button','关闭','copy-button');
    close.onclick=()=>dialog.close();
    dialog.append(heading,help,field,close);
    document.body.append(dialog);
    dialog.addEventListener('close',()=>dialog.remove(),{once:true});
    dialog.showModal();
    field.focus();
    field.select();
  }
}

function pauseVideos() { $$('video').forEach(video => video.pause()); }
function setVideo(video, version) {
  video.pause();
  video.preload = 'auto';
  video.poster = version.poster;
  video.src = version.clip;
  video.setAttribute('aria-label',`V${version.id} ${version.name}，${version.length} 秒片段`);
  video.load();
}
function sizeStage() {
  const viewport = $('#viewport');
  const scale = Math.min(viewport.clientWidth / 1440, viewport.clientHeight / 810);
  document.documentElement.style.setProperty('--scale', String(scale));
}
function pageFromHash() {
  const number = Number(location.hash.slice(1));
  return Number.isInteger(number) && number >= 1 && number <= slides.length ? number - 1 : 0;
}
function go(index, updateHash = true) {
  current = Math.max(0, Math.min(index, slides.length - 1));
  pauseVideos();
  slides.forEach((slide, i) => {
    slide.hidden = i !== current;
    slide.classList.toggle('entering', i === current);
  });
  $('#page-count').textContent = `${String(current + 1).padStart(2,'0')} / ${slides.length}`;
  $('#chapter-name').textContent = slides[current].dataset.title;
  document.title = `${current + 1}. ${slides[current].dataset.title} · Opus 5.5 视频分享`;
  $('#prev').disabled = current === 0;
  $('#next').disabled = current === slides.length - 1;
  $$('#progress-dots button').forEach((button,i)=>button.setAttribute('aria-current',String(i === current)));
  $('#note-heading').textContent = notes[current][0];
  $('#note-content').textContent = notes[current][1];
  $('#note-source').textContent = notes[current][2];
  if (updateHash && location.hash !== `#${current + 1}`) history.replaceState(null,'',`#${current + 1}`);
  if (matchMedia('(max-width:760px)').matches) window.scrollTo({top:0,behavior:'instant'});
}
function selectVersion(id) {
  selectedVersion = id;
  const version = versions.find(v=>v.id === id);
  setVideo($('#screening-video'),version);
  $('#screening-title').textContent = `V${id} · ${version.name}`;
  $('#screening-description').textContent = version.description;
  $('#screening-meta').textContent = `原片 ${version.duration}　/　${version.sound}　/　本地片段 ${version.length} 秒（${Math.floor(version.start/60)}:${String(version.start%60).padStart(2,'0')} 起）`;
  $$('#version-menu button').forEach(button=>button.setAttribute('aria-pressed',String(Number(button.dataset.version) === id)));
}
function openDetail(id) {
  detailVersion = versions.find(v=>v.id === id);
  pauseVideos();
  $('#detail-title').textContent = `V${id} · ${detailVersion.name}`;
  $('#detail-meta').textContent = `原片 ${detailVersion.duration} / ${detailVersion.sound} / 预览 ${detailVersion.length} 秒`;
  $('#detail-description').textContent = detailVersion.description;
  $('#detail-prompt').value = detailVersion.prompt;
  $('#detail-sheet').src = detailVersion.sheet;
  $('#detail-sheet').alt = `V${id} ${detailVersion.name}的成片截图拼图`;
  $('#media-error').hidden = true;
  setVideo($('#detail-video'),detailVersion);
  $('#detail-dialog').showModal();
  $('#detail-dialog').scrollTop = 0;
}
function chooseSound(id) {
  const version = versions.find(v=>v.id === id);
  setVideo($('#sound-video'),version);
  $('#sound-description').textContent = `${version.sound}。${version.description}`;
  $$('#sound-options button').forEach(button=>button.setAttribute('aria-pressed',String(Number(button.dataset.version) === id)));
}
function chooseFeedback(index) {
  selectedFeedback = index;
  const item = feedback[index];
  $('#feedback-quote').textContent = item.quote;
  $('#feedback-quote').style.whiteSpace = 'pre-line';
  $('#feedback-action').textContent = item.action;
  $('#feedback-explain').textContent = item.explain;
  $$('#feedback-tabs button').forEach((button,i)=>button.setAttribute('aria-pressed',String(i === index)));
}
function buildPrompt() {
  const path = $('#material-path').value.trim() || '【我的素材文件夹路径】';
  $('#built-prompt').value = `请根据我的资料，为我制作一条视频：在你的视角里，我是一个什么样的人。\n\n资料在：${path}\n（内含聊天记录、笔记、项目记录和头像。）\n\n用真实数据和原话，引用标日期并核对。统计活跃时间只用时间字段，引用原话再核对原文。\n\n风格：${selectedStyle.prompt}\n\n用 Remotion 等合适的工具制作。请先给我关键帧；涉及节奏时先出一段 15 秒样片，我确认后再渲染整片。`;
}
function toggleNotes() {
  const panel = $('#speaker-notes');
  panel.hidden = !panel.hidden;
  $('#notes-toggle').setAttribute('aria-expanded',String(!panel.hidden));
}
async function toggleFullscreen() {
  try {
    if (document.fullscreenElement) await document.exitFullscreen();
    else if (document.documentElement.requestFullscreen) await document.documentElement.requestFullscreen();
    else toast('此浏览器未提供全屏功能，请使用浏览器菜单进入全屏');
  } catch { toast('未能进入全屏，请使用浏览器菜单中的全屏选项'); }
}

slides.forEach((slide,index)=>{
  const dot = element('button');
  dot.setAttribute('aria-label',`第 ${index+1} 页：${slide.dataset.title}`);
  dot.title = `${index+1} / ${slide.dataset.title}`;
  dot.onclick = ()=>go(index);
  $('#progress-dots').append(dot);
  const item = element('button');
  item.append(element('span',String(index+1).padStart(2,'0')),element('div',slide.dataset.title));
  item.onclick = ()=>{ $('#contents-dialog').close(); go(index); };
  $('#contents-grid').append(item);
});
versions.forEach(version=>{
  const button = element('button');
  button.dataset.version = version.id;
  button.setAttribute('aria-pressed','false');
  button.append(element('span',`V${String(version.id).padStart(2,'0')}`),document.createTextNode(version.name));
  button.onclick = ()=>selectVersion(version.id);
  $('#version-menu').append(button);
});
versions.slice(0,4).forEach(version=>{
  const button = element('button');
  button.dataset.version = version.id;
  button.setAttribute('aria-pressed','false');
  button.append(element('span',`V${version.id}`),document.createTextNode(version.id === 1 ? '只有配乐' : version.name));
  button.onclick = ()=>chooseSound(version.id);
  $('#sound-options').append(button);
});
styles.forEach(style=>{
  const version = versions.find(v=>v.id === style.id);
  const card = element('button',undefined,'style-card');
  const image = element('img');
  image.src = version.poster;
  image.alt = `${version.name}版成片画面`;
  const heading = element('div');
  heading.append(element('h3',style.label),element('span',`V${style.id} ↗`));
  card.append(image,heading,element('p',style.rule));
  card.setAttribute('aria-label',`查看${style.label}版截图与完整提示词`);
  card.onclick = ()=>openDetail(style.id);
  $('#style-grid').append(card);
  const choice = element('button',style.label);
  choice.dataset.style = style.id;
  choice.setAttribute('aria-pressed',String(style.id === selectedStyle.id));
  choice.onclick = ()=>{
    selectedStyle = style;
    $$('#builder-options button').forEach(button=>button.setAttribute('aria-pressed',String(Number(button.dataset.style) === style.id)));
    buildPrompt();
  };
  $('#builder-options').append(choice);
});
feedback.forEach((item,index)=>{
  const button = element('button',item.label);
  button.setAttribute('aria-pressed','false');
  button.onclick = ()=>chooseFeedback(index);
  $('#feedback-tabs').append(button);
});
$$('[data-goto]').forEach(button=>button.onclick = ()=>go(Number(button.dataset.goto)-1));
$$('[data-detail]').forEach(button=>button.onclick = ()=>openDetail(Number(button.dataset.detail)));
$$('[data-close]').forEach(button=>button.onclick = ()=>button.closest('dialog').close());
$$('dialog').forEach(dialog=>{
  dialog.addEventListener('close',()=>$$('video',dialog).forEach(video=>video.pause()));
  dialog.addEventListener('click',event=>{
    if (event.target !== dialog) return;
    const box = dialog.getBoundingClientRect();
    if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) dialog.close();
  });
});
$$('video').forEach(video=>{
  video.addEventListener('play',()=>$$('video').filter(other=>other!==video).forEach(other=>other.pause()));
  video.addEventListener('error',()=>{
    if(video.id === 'detail-video') $('#media-error').hidden = false;
    toast('视频未能加载，请保留同目录的 assets 文件夹');
  });
});
$('#prev').onclick = ()=>go(current-1);
$('#next').onclick = ()=>go(current+1);
$('#overview').onclick = ()=>{pauseVideos();$('#contents-dialog').showModal();};
$('#notes-toggle').onclick = toggleNotes;
$('#close-notes').onclick = toggleNotes;
$('#fullscreen').onclick = toggleFullscreen;
$('#screening-detail').onclick = ()=>openDetail(selectedVersion);
$('#copy-detail').onclick = ()=>copyText(detailVersion.prompt);
$('[data-copy=starter]').onclick = ()=>copyText(starter);
$('#copy-feedback').onclick = ()=>copyText(feedback[selectedFeedback].copy);
$('#copy-built').onclick = ()=>copyText($('#built-prompt').value);
$('#material-path').addEventListener('input',buildPrompt);
$('#open-studies').onclick = ()=>$('#image-dialog').showModal();
document.addEventListener('keydown',event=>{
  if (event.ctrlKey || event.metaKey || event.altKey || $('dialog[open]')) return;
  if (event.target.closest('input,textarea,select,video,[contenteditable=true]')) return;
  if (event.code === 'Space' && event.target.closest('button,a')) return;
  if (['ArrowRight','ArrowDown','PageDown',' '].includes(event.key)) {event.preventDefault();go(current+1);}
  else if (['ArrowLeft','ArrowUp','PageUp'].includes(event.key)) {event.preventDefault();go(current-1);}
  else if (event.key === 'Home') {event.preventDefault();go(0);}
  else if (event.key === 'End') {event.preventDefault();go(slides.length-1);}
  else if (event.key.toLowerCase() === 'o') {pauseVideos();$('#contents-dialog').showModal();}
  else if (event.key.toLowerCase() === 'n') toggleNotes();
  else if (event.key.toLowerCase() === 'f') toggleFullscreen();
  else if (event.key === 'Escape' && !$('#speaker-notes').hidden) toggleNotes();
});
document.addEventListener('visibilitychange',()=>{if(document.hidden) pauseVideos();});
window.addEventListener('hashchange',()=>go(pageFromHash(),false));
window.addEventListener('resize',sizeStage);
document.addEventListener('fullscreenchange',()=>{
  $('#fullscreen').textContent = document.fullscreenElement ? '退出全屏' : '全屏 F';
  sizeStage();
});
selectVersion(11);
chooseSound(2);
chooseFeedback(0);
buildPrompt();
sizeStage();
go(pageFromHash(),false);
