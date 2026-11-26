/**
 * Boletim Empresarial Diário — inscrição, confirmação, envio e cancelamento.
 * Projeto Apps Script da conta atendimento@soleoconsultoria.com.br (Google Workspace).
 *
 * Implantação: Implantar > Nova implantação > App da Web
 *   Executar como: Eu (atendimento@) · Quem pode acessar: Qualquer pessoa
 * Depois de implantar, rodar configurar() uma vez (cria a planilha e o gatilho de 30 em 30 min).
 *
 * Fluxo diário: a tarefa agendada publica a edição no site (boletim/feed.json).
 * enviarEdicao() roda a cada 30 min das 6h às 20h; quando o item mais recente do feed é de hoje
 * e ainda não foi enviado, manda o e-mail a cada inscrito ativo, em lotes, retomando de onde parou.
 */
var CFG = {
  FEED_URL: 'https://www.soleoconsultoria.com.br/boletim/feed.json',
  SITE: 'https://www.soleoconsultoria.com.br',
  NOME_REMETENTE: 'Soléo Consultoria Empresarial',
  RESPONDER_PARA: 'marcos@soleoconsultoria.com.br',
  AVISAR: 'marcos@soleoconsultoria.com.br',
  TZ: 'America/Sao_Paulo',
  JANELA_INICIO: 6,
  JANELA_FIM: 20,
  LOTE_MAX: 90,
  RESERVA_COTA: 20
};
var ABA = 'Inscritos';
var ABA_ENV = 'Envios';
var COLS = ['email', 'nome', 'empresa', 'status', 'token', 'origem', 'inscrito_em', 'confirmado_em', 'cancelado_em', 'ultima_edicao', 'enviados', 'confirmacao_enviada_em'];

function props_() { return PropertiesService.getScriptProperties(); }
function agora_() { return Utilities.formatDate(new Date(), CFG.TZ, 'yyyy-MM-dd HH:mm:ss'); }
function hoje_() { return Utilities.formatDate(new Date(), CFG.TZ, 'yyyy-MM-dd'); }

function planilha_() {
  var id = props_().getProperty('SHEET_ID');
  if (!id) throw new Error('Rode configurar() antes.');
  return SpreadsheetApp.openById(id);
}

/** Rodar uma vez após a primeira implantação. */
function configurar() {
  var id = props_().getProperty('SHEET_ID');
  if (!id) {
    var ss = SpreadsheetApp.create('Boletim Empresarial Diário · Inscritos');
    id = ss.getId();
    props_().setProperty('SHEET_ID', id);
    var sh = ss.getSheets()[0];
    sh.setName(ABA);
    sh.getRange(1, 1, 1, COLS.length).setValues([COLS]).setFontWeight('bold');
    sh.setFrozenRows(1);
    var env = ss.insertSheet(ABA_ENV);
    env.getRange(1, 1, 1, 6).setValues([['data_hora', 'edicao', 'enviados', 'falhas', 'restantes', 'obs']]).setFontWeight('bold');
    env.setFrozenRows(1);
    try { DriveApp.getFileById(id).addEditor(CFG.AVISAR); } catch (e) {}
  }
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === 'enviarEdicao') ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger('enviarEdicao').timeBased().everyMinutes(30).create();
  Logger.log('Planilha: https://docs.google.com/spreadsheets/d/' + id + '/edit');
  return id;
}

function webappUrl_() {
  var u = '';
  try { u = ScriptApp.getService().getUrl() || ''; } catch (e) {}
  if (/\/exec$/.test(u)) { props_().setProperty('WEBAPP_URL', u); return u; }
  return props_().getProperty('WEBAPP_URL') || u;
}

// ------------------------------------------------------------------ web app
function doPost(e) {
  webappUrl_();
  var r = inscrever_((e && e.parameter) || {});
  return ContentService.createTextOutput(JSON.stringify(r)).setMimeType(ContentService.MimeType.JSON);
}

function doGet(e) {
  webappUrl_();
  var p = (e && e.parameter) || {};
  if (p.a === 'confirmar') return pagina_(confirmar_(p.t));
  if (p.a === 'sair') return pagina_(cancelar_(p.t));
  return pagina_({ ok: true, titulo: 'Boletim Empresarial Diário', msg: 'Para se inscrever, acesse a página do boletim.' });
}

function linhas_() {
  var sh = planilha_().getSheetByName(ABA);
  var v = sh.getDataRange().getValues();
  return { sh: sh, head: v[0], rows: v.slice(1) };
}

function col_(nome) { return COLS.indexOf(nome); }

function acharPor_(campo, valor) {
  var d = linhas_();
  var c = col_(campo);
  for (var i = 0; i < d.rows.length; i++) {
    if (String(d.rows[i][c]).toLowerCase() === String(valor).toLowerCase()) return { d: d, i: i, row: d.rows[i], linha: i + 2 };
  }
  return { d: d, i: -1 };
}

function set_(sh, linha, campo, valor) { sh.getRange(linha, col_(campo) + 1).setValue(valor); }

function inscrever_(p) {
  var email = String(p.email || '').trim().toLowerCase();
  if (p.website) return { ok: true };
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email)) return { ok: false, msg: 'E-mail inválido.' };
  if (p.aceite !== 'sim') return { ok: false, msg: 'Marque o aceite para se inscrever.' };
  var lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    var f = acharPor_('email', email);
    var sh = f.d.sh;
    var token;
    if (f.i >= 0) {
      var st = f.row[col_('status')];
      if (st === 'ativo') return { ok: true, titulo: 'Você já está inscrito', msg: 'Este e-mail já recebe o boletim.' };
      token = f.row[col_('token')] || Utilities.getUuid();
      var ult = f.row[col_('confirmacao_enviada_em')];
      if (st === 'pendente' && ult && (new Date() - new Date(ult)) < 10 * 60 * 1000) return { ok: true, titulo: 'Confira seu e-mail', msg: 'O link de confirmação já foi enviado.' };
      set_(sh, f.linha, 'status', 'pendente');
      set_(sh, f.linha, 'token', token);
      if (p.nome) set_(sh, f.linha, 'nome', String(p.nome).slice(0, 120));
      if (p.empresa) set_(sh, f.linha, 'empresa', String(p.empresa).slice(0, 160));
      set_(sh, f.linha, 'confirmacao_enviada_em', new Date());
    } else {
      token = Utilities.getUuid();
      var nova = COLS.map(function () { return ''; });
      nova[col_('email')] = email;
      nova[col_('nome')] = String(p.nome || '').slice(0, 120);
      nova[col_('empresa')] = String(p.empresa || '').slice(0, 160);
      nova[col_('status')] = 'pendente';
      nova[col_('token')] = token;
      nova[col_('origem')] = String(p.origem || '').slice(0, 60);
      nova[col_('inscrito_em')] = agora_();
      nova[col_('enviados')] = 0;
      nova[col_('confirmacao_enviada_em')] = new Date();
      sh.appendRow(nova);
    }
    enviarConfirmacao_(email, String(p.nome || ''), token);
    return { ok: true, titulo: 'Confira seu e-mail', msg: 'Enviamos o link de confirmação.' };
  } finally {
    lock.releaseLock();
  }
}

function enviarConfirmacao_(email, nome, token) {
  var url = webappUrl_() + '?a=confirmar&t=' + encodeURIComponent(token);
  var ola = nome ? 'Olá, ' + nome.split(' ')[0] + '.' : 'Olá.';
  var html = moldura_(
    '<p style="margin:0 0 14px;font:16px/1.6 Arial,sans-serif;color:#1f2937">' + ola + '</p>' +
    '<p style="margin:0 0 18px;font:16px/1.6 Arial,sans-serif;color:#1f2937">Confirme sua inscrição no <b>Boletim Empresarial Diário</b> para receber, todo dia às 7h, um artigo de direito empresarial e o radar dos tribunais.</p>' +
    botao_(url, 'Confirmar inscrição') +
    '<p style="margin:18px 0 0;font:13px/1.6 Arial,sans-serif;color:#6b7280">Se você não pediu a inscrição, ignore este e-mail.</p>');
  GmailApp.sendEmail(email, 'Confirme sua inscrição no Boletim Empresarial Diário',
    ola + '\n\nConfirme sua inscrição no Boletim Empresarial Diário: ' + url + '\n\nSe você não pediu a inscrição, ignore este e-mail.',
    { htmlBody: html, name: CFG.NOME_REMETENTE, replyTo: CFG.RESPONDER_PARA });
}

function confirmar_(token) {
  if (!token) return { ok: false, titulo: 'Link inválido', msg: 'O link de confirmação está incompleto.' };
  var f = acharPor_('token', token);
  if (f.i < 0) return { ok: false, titulo: 'Link inválido', msg: 'Não encontramos esta inscrição. Inscreva-se de novo na página do boletim.' };
  var sh = f.d.sh;
  if (f.row[col_('status')] !== 'ativo') {
    set_(sh, f.linha, 'status', 'ativo');
    set_(sh, f.linha, 'confirmado_em', agora_());
    set_(sh, f.linha, 'cancelado_em', '');
    try {
      MailApp.sendEmail(CFG.AVISAR, 'Boletim: nova inscrição confirmada — ' + f.row[col_('email')],
        'E-mail: ' + f.row[col_('email')] + '\nNome: ' + f.row[col_('nome')] + '\nEmpresa: ' + f.row[col_('empresa')] + '\nOrigem: ' + f.row[col_('origem')] +
        '\nPlanilha: https://docs.google.com/spreadsheets/d/' + props_().getProperty('SHEET_ID') + '/edit');
    } catch (e) {}
  }
  return { ok: true, titulo: 'Inscrição confirmada', msg: 'A partir da próxima edição, o boletim chega no seu e-mail por volta das 7h.', link: CFG.SITE + '/boletim/', rotulo: 'Ler as edições publicadas' };
}

function cancelar_(token) {
  if (!token) return { ok: false, titulo: 'Link inválido', msg: 'O link de cancelamento está incompleto.' };
  var f = acharPor_('token', token);
  if (f.i < 0) return { ok: false, titulo: 'Link inválido', msg: 'Não encontramos esta inscrição.' };
  set_(f.d.sh, f.linha, 'status', 'cancelado');
  set_(f.d.sh, f.linha, 'cancelado_em', agora_());
  return { ok: true, titulo: 'Inscrição cancelada', msg: 'Você não receberá mais o Boletim Empresarial Diário. Se mudar de ideia, é só se inscrever de novo.', link: CFG.SITE + '/boletim/', rotulo: 'Página do boletim' };
}

function pagina_(r) {
  var cor = r.ok === false ? '#7f1d1d' : '#0b1d40';
  var link = r.link ? '<p style="margin:22px 0 0"><a target="_top" href="' + r.link + '" style="display:inline-block;background:#c89f54;color:#0b1d40;font:bold 16px Arial,sans-serif;text-decoration:none;padding:13px 22px;border-radius:4px">' + r.rotulo + '</a></p>' : '';
  var html = '<div style="min-height:100vh;margin:0;background:#efe9dc;padding:40px 16px;box-sizing:border-box;font-family:Arial,sans-serif">' +
    '<div style="max-width:560px;margin:0 auto;background:#fff;border-radius:6px;overflow:hidden;box-shadow:0 18px 40px rgba(11,29,64,.15)">' +
    '<div style="background:#0b1d40;border-bottom:4px solid #c89f54;padding:20px 26px;font:bold 12px Arial;letter-spacing:.14em;text-transform:uppercase;color:#e2c48a">Boletim Empresarial Diário</div>' +
    '<div style="padding:28px 26px"><h1 style="margin:0 0 10px;font:bold 26px/1.25 Georgia,serif;color:' + cor + '">' + r.titulo + '</h1>' +
    '<p style="margin:0;font:16px/1.6 Arial,sans-serif;color:#1f2937">' + r.msg + '</p>' + link + '</div>' +
    '<div style="padding:14px 26px;background:#0b1220;font:12px Arial;color:#cbd5e1">Soléo Consultoria Empresarial · soleoconsultoria.com.br</div></div></div>';
  return HtmlService.createHtmlOutput(html).setTitle(r.titulo + ' · Boletim Empresarial Diário').addMetaTag('viewport', 'width=device-width, initial-scale=1');
}

function moldura_(conteudo) {
  return '<div style="background:#efe9dc;padding:24px 12px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;margin:0 auto;background:#fff;border-radius:6px">' +
    '<tr><td style="background:#0b1d40;border-bottom:4px solid #c89f54;padding:20px 26px;font:bold 12px Arial,sans-serif;letter-spacing:.14em;text-transform:uppercase;color:#e2c48a">Boletim Empresarial Diário</td></tr>' +
    '<tr><td style="padding:26px">' + conteudo + '</td></tr>' +
    '<tr><td style="background:#0b1220;padding:14px 26px;font:12px Arial,sans-serif;color:#cbd5e1">Soléo Consultoria Empresarial · CNPJ 68.804.940/0001-77 · soleoconsultoria.com.br</td></tr></table></div>';
}

function botao_(url, texto) {
  return '<table role="presentation" cellpadding="0" cellspacing="0"><tr><td bgcolor="#c89f54" style="border-radius:4px"><a href="' + url + '" style="display:inline-block;padding:13px 22px;font:bold 16px Arial,sans-serif;color:#0b1d40;text-decoration:none">' + texto + '</a></td></tr></table>';
}

// ------------------------------------------------------------------ envio diário
function edicaoDoDia_() {
  var r = UrlFetchApp.fetch(CFG.FEED_URL + '?t=' + Date.now(), { muteHttpExceptions: true });
  if (r.getResponseCode() !== 200) return null;
  var feed = JSON.parse(r.getContentText());
  var it = feed.items && feed.items[0];
  if (!it || !it._soleo || it._soleo.data !== hoje_()) return null;
  return it;
}

function baixar_(url) {
  var r = UrlFetchApp.fetch(url + '?t=' + Date.now(), { muteHttpExceptions: true });
  if (r.getResponseCode() !== 200) return null;
  return r.getContentText('UTF-8');
}

function enviarEdicao() {
  var h = Number(Utilities.formatDate(new Date(), CFG.TZ, 'H'));
  if (h < CFG.JANELA_INICIO || h >= CFG.JANELA_FIM) return;
  var lock = LockService.getScriptLock();
  if (!lock.tryLock(1000)) return;
  try {
    var it = edicaoDoDia_();
    if (!it) return;
    var chave = 'ENVIADA_' + it.id;
    if (props_().getProperty(chave) === 'ok') return;
    var html = baixar_(it._soleo.email_url);
    var txt = baixar_(it._soleo.texto_url) || '';
    if (!html || html.indexOf('{{DESCADASTRO}}') < 0) { registrar_(it.id, 0, 0, -1, 'e-mail da edição indisponível'); return; }
    var d = linhas_();
    var cS = col_('status'), cU = col_('ultima_edicao');
    var fila = [];
    d.rows.forEach(function (row, i) { if (row[cS] === 'ativo' && row[cU] !== it.id) fila.push(i); });
    if (!fila.length) { props_().setProperty(chave, 'ok'); registrar_(it.id, 0, 0, 0, 'sem inscritos pendentes'); return; }
    var cota = MailApp.getRemainingDailyQuota() - CFG.RESERVA_COTA;
    var lote = Math.max(0, Math.min(fila.length, CFG.LOTE_MAX, cota));
    var ok = 0, falhas = 0, t0 = Date.now();
    var base = webappUrl_();
    for (var k = 0; k < lote; k++) {
      if (Date.now() - t0 > 4.5 * 60 * 1000) break;
      var i = fila[k], row = d.rows[i], linha = i + 2;
      var nome = String(row[col_('nome')] || '').trim().split(' ')[0];
      var sair = base + '?a=sair&t=' + encodeURIComponent(row[col_('token')]);
      var corpo = html.split('{{DESCADASTRO}}').join(sair).split('{{NOME}}').join(nome ? ', ' + nome : '');
      var texto = txt.split('{{DESCADASTRO}}').join(sair);
      try {
        GmailApp.sendEmail(row[col_('email')], it._soleo.assunto, texto, { htmlBody: corpo, name: CFG.NOME_REMETENTE, replyTo: CFG.RESPONDER_PARA });
        d.sh.getRange(linha, cU + 1).setValue(it.id);
        d.sh.getRange(linha, col_('enviados') + 1).setValue(Number(row[col_('enviados')] || 0) + 1);
        ok++;
      } catch (e) {
        falhas++;
      }
    }
    var restantes = fila.length - ok;
    if (restantes <= 0) props_().setProperty(chave, 'ok');
    registrar_(it.id, ok, falhas, restantes, cota <= 0 ? 'cota diária esgotada' : '');
  } finally {
    lock.releaseLock();
  }
}

function registrar_(edicao, ok, falhas, restantes, obs) {
  planilha_().getSheetByName(ABA_ENV).appendRow([agora_(), edicao, ok, falhas, restantes, obs || '']);
}

/** Envia a edição mais recente do feed só para CFG.AVISAR (teste). */
function testarEnvio() {
  var r = JSON.parse(UrlFetchApp.fetch(CFG.FEED_URL + '?t=' + Date.now()).getContentText());
  var it = r.items[0];
  var html = baixar_(it._soleo.email_url);
  var sair = webappUrl_() + '?a=sair&t=teste';
  GmailApp.sendEmail(CFG.AVISAR, '[TESTE] ' + it._soleo.assunto, (baixar_(it._soleo.texto_url) || '').split('{{DESCADASTRO}}').join(sair),
    { htmlBody: html.split('{{DESCADASTRO}}').join(sair).split('{{NOME}}').join(', Marcos'), name: CFG.NOME_REMETENTE, replyTo: CFG.RESPONDER_PARA });
}
