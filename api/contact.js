// api/contact.js — fonction serverless Vercel (Node 18+)
const TO = ['jfboyer@bvtech.fr', 'hillion.joris00@gmail.com'];
const FROM = 'CastMate <contact@send.castmate.fr>'; // domaine à vérifier dans Resend

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ ok: false });
  try {
    const { name = '', email = '', message = '', company = '', phone = '',
            _form = 'contact', _gotcha = '' } = req.body || {};
    if (_gotcha) return res.status(200).json({ ok: true }); // honeypot anti-spam
    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email))
      return res.status(400).json({ ok: false, error: 'email' });

    const isDemo = _form === 'demo';
    const subject = `${isDemo ? 'Demande de démo' : 'Contact'} CastMate — ${name || email}`;
    const html = `
      <h2>${isDemo ? 'Demande de démo' : 'Message de contact'} — CastMate</h2>
      <p><strong>Nom :</strong> ${esc(name) || '—'}</p>
      <p><strong>Email :</strong> ${esc(email)}</p>
      ${company ? `<p><strong>Société :</strong> ${esc(company)}</p>` : ''}
      ${phone ? `<p><strong>Téléphone :</strong> ${esc(phone)}</p>` : ''}
      ${message ? `<p><strong>Message :</strong><br>${esc(message).replace(/\n/g,'<br>')}</p>` : ''}`;

    const r = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: { Authorization: `Bearer ${process.env.RESEND_API_KEY}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ from: FROM, to: TO, reply_to: email, subject, html }),
    });
    if (!r.ok) { console.error('Resend', r.status, await r.text()); return res.status(502).json({ ok: false }); }
    return res.status(200).json({ ok: true });
  } catch (e) { console.error(e); return res.status(500).json({ ok: false }); }
}
function esc(s = '') {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
