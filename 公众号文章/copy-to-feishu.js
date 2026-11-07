(() => {
  function init() {
    const toolbar = document.querySelector('.feishu-tools');
    if (!toolbar || toolbar.dataset.ready) return;
    toolbar.dataset.ready = 'true';
    const button = toolbar.querySelector('button');
    const status = toolbar.querySelector('[role="status"]');

    function articlePayload() {
      const article = document.querySelector('main').cloneNode(true);
      article.querySelectorAll('.expand').forEach(node => {
        node.replaceWith(...node.childNodes);
      });
      article.querySelectorAll('button,script,style,dialog,.feishu-tools,.hint').forEach(node => node.remove());
      // Keep the GIF fallback, not the higher-resolution WebP preview.
      article.querySelectorAll('picture').forEach(node => node.replaceWith(node.querySelector('img')));
      article.querySelectorAll('img').forEach(img => {
        const width = Number(img.getAttribute('width')) || 720;
        const height = Number(img.getAttribute('height'));
        const targetWidth = img.closest('.qr') ? 145 : Math.min(width, 720);
        img.setAttribute('width', String(targetWidth));
        if (height) img.setAttribute('height', String(Math.round(height * targetWidth / width)));
        img.removeAttribute('loading');
        img.removeAttribute('srcset');
        img.removeAttribute('sizes');
        img.style.cssText = 'display:block;max-width:100%;height:auto;margin:16px 0;';
      });
      const styles = {
        h1: 'font-size:28px;line-height:1.4;margin:0 0 20px;font-weight:700;',
        h2: 'font-size:23px;line-height:1.5;margin:32px 0 14px;font-weight:700;',
        h3: 'font-size:20px;line-height:1.5;margin:24px 0 10px;font-weight:700;',
        p: 'margin:14px 0;line-height:1.8;',
        figure: 'display:block;margin:24px 0;',
        figcaption: 'font-size:14px;color:#526057;line-height:1.7;margin:8px 0 20px;',
        blockquote: 'margin:20px 0;padding:12px 18px;border-left:3px solid #9c3428;background:#f8f3e9;',
        a: 'color:#285e58;text-decoration:underline;',
        li: 'margin:8px 0;line-height:1.8;',
      };
      article.querySelectorAll('*').forEach(node => {
        const style = styles[node.tagName.toLowerCase()];
        if (style) node.style.cssText = style;
        node.removeAttribute('class');
        node.removeAttribute('id');
      });

      const plain = article.cloneNode(true);
      plain.querySelectorAll('img').forEach(img => img.replaceWith(`\n[配图：${img.alt || '文章配图'}]\n`));
      plain.querySelectorAll('a[href]').forEach(link => {
        const href = link.getAttribute('href');
        if (href && link.textContent.trim() !== href) link.append(`（${href}）`);
      });
      plain.querySelectorAll('h1,h2,h3,p,figure,figcaption,blockquote,li').forEach(node => node.append('\n\n'));
      const text = plain.textContent.replace(/[ \t]+\n/g, '\n').replace(/\n{3,}/g, '\n\n').trim();
      const html = `<html><head><meta charset="utf-8"></head><body><!--StartFragment--><article style="font-family:Arial,'PingFang SC',sans-serif;font-size:16px;line-height:1.8;color:#17231e;">${article.innerHTML}</article><!--EndFragment--></body></html>`;
      return {html, text};
    }

    function legacyCopy(payload) {
      const input = document.createElement('textarea');
      input.value = payload.text;
      input.setAttribute('aria-label', '复制正文');
      input.style.cssText = 'position:fixed;left:-9999px;top:0;';
      document.body.append(input);
      input.select();
      let handled = false;
      const onCopy = event => {
        if (!event.clipboardData) return;
        event.clipboardData.setData('text/html', payload.html);
        event.clipboardData.setData('text/plain', payload.text);
        event.preventDefault();
        handled = true;
      };
      document.addEventListener('copy', onCopy);
      try {
        return document.execCommand('copy') && handled;
      } catch {
        return false;
      } finally {
        document.removeEventListener('copy', onCopy);
        input.remove();
        button.focus();
      }
    }

    function manualCopy(payload) {
      const dialog = document.createElement('dialog');
      dialog.className = 'feishu-manual';
      dialog.setAttribute('aria-label', '手动复制文章');
      const instructions = document.createElement('p');
      instructions.textContent = '自动复制被浏览器拦截。下方正文已选中，请按 ⌘C / Ctrl+C，再到飞书按 ⌘V / Ctrl+V。';
      const close = document.createElement('button');
      close.type = 'button';
      close.textContent = '关闭';
      const select = document.createElement('button');
      select.type = 'button';
      select.textContent = '重新选中全文';
      const content = document.createElement('div');
      content.className = 'feishu-manual-content';
      const parsed = new DOMParser().parseFromString(payload.html, 'text/html');
      content.append(...parsed.body.childNodes);
      dialog.append(instructions, select, close, content);
      document.body.append(dialog);
      const selectAll = () => {
        const range = document.createRange();
        range.selectNodeContents(content);
        const selection = window.getSelection();
        selection.removeAllRanges();
        selection.addRange(range);
      };
      select.addEventListener('click', selectAll);
      close.addEventListener('click', () => dialog.close());
      dialog.addEventListener('close', () => {dialog.remove(); button.focus();}, {once:true});
      dialog.showModal();
      selectAll();
    }

    button.addEventListener('click', async () => {
      if (button.disabled) return;
      button.disabled = true;
      button.textContent = '正在复制…';
      toolbar.setAttribute('aria-busy', 'true');
      status.textContent = '正在准备全文和配图…';
      try {
        const payload = articlePayload();
        let copied = false;
        if (navigator.clipboard?.write && typeof ClipboardItem !== 'undefined') {
          try {
            await navigator.clipboard.write([new ClipboardItem({
              'text/html': new Blob([payload.html], {type:'text/html'}),
              'text/plain': new Blob([payload.text], {type:'text/plain'}),
            })]);
            copied = true;
          } catch { /* Local files and browser permissions may require the fallback. */ }
        }
        if (!copied) copied = legacyCopy(payload);
        if (copied) {
          status.textContent = '已复制图文。打开飞书文档，点击正文位置，按 ⌘V / Ctrl+V 粘贴；图片较多，请等待上传完成。';
        } else {
          status.textContent = '自动复制未成功，请在弹出的窗口中手动复制。';
          manualCopy(payload);
        }
      } catch {
        status.textContent = '复制未完成，请刷新页面后重试。';
      } finally {
        button.disabled = false;
        button.textContent = '复制到飞书';
        toolbar.removeAttribute('aria-busy');
      }
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, {once:true});
  else init();
})();
