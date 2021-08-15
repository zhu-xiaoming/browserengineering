/**
 * This file compiles the code in Web Browser Engineering,
 * up to and including Chapter 1 (Downloading Web Pages)
 */

import assert from 'assert';
import net from 'net';
import { platform } from 'os';
import tls from 'tls';

let redirectsTimes = 0;

async function request(url: string) {
  const [scheme, ...other] = url.split('://');
  url = other.join('://');

  assert.ok(['http', 'https'].includes(scheme), `Unknown scheme ${scheme}`);

  let host: string;
  let path: string;
  if (url.includes('/')) {
    const res = url.split('/');
    host = res[0];
    path = `/${res.slice(1).join('/')}`;
  } else {
    host = url;
    path = '/';
  }

  let port = scheme === 'http' ? 80 : 443;

  if (host.includes(':')) {
    const res = host.split(':');
    host = res[0];
    port = Number(res.slice(1).join(':'));
  }

  let s = net.connect({
    host,
    port,
  });

  if (scheme === 'https') {
    s = tls.connect({
      socket: s,
      servername: host,
    });
  }

  s.once('connect', (stream) => {
    s.write(`GET ${path} HTTP/1.0\r\n`);
    s.write(`Host: ${host}\r\n`);
    s.write('Connection: close\r\n');
    s.write(`User-Agent: Mozilla/5.0 (${platform()})\r\n`);
    s.write('\r\n');
    // s.end('\r\n');
  });
  s.on('close', () => {
    console.log('socket close')
  })
  s.on('error', err => {
    console.log('socket error:', err)
  });

  const response = await new Promise<string>((resolve) => {
    let resp = '';
    s.on('data', (data) => {
      resp += data.toString('utf8')
    });
    s.on('end', () => {
      resolve(resp)
    })
  });

  const [statusLine, ...otherLines] = response.split('\r\n');
  const statusLineSplit = statusLine.split(' ');
  const status = statusLineSplit[1];
  const explanation = statusLineSplit.slice(2).join(' ');
  assert.ok(['200', '301', '302'].includes(status), `${status}: ${explanation}`);

  const headers: any = {};
  const firstEmptyLineIndex = otherLines.findIndex((e) => !e);
  const headersLines = otherLines.slice(0, firstEmptyLineIndex);
  const bodyLines = otherLines.slice(firstEmptyLineIndex + 1);

  headersLines.forEach((line) => {
    const res = line.split(':');
    const header = res[0];
    const value = res.slice(1).join(':');
    headers[header.toLowerCase()] = value.trim();
  });

  if (['301', '302'].includes(status)) {
    if (redirectsTimes > 10) {
      throw new Error('redirects times > 10 !')
    }
    if (!headers.location) {
      throw new Error('no headers.location')
    }
    redirectsTimes += 1;
    return request(headers.location)
  } else {
    redirectsTimes = 0;
  }

  const body = bodyLines.join('\r\n');
  // s.destroy();
  return {
    headers,
    body,
  };
}

class Text {
  text: string;

  constructor(text: string) {
    this.text = text;
  }
}

class Tag {
  tag: string;

  constructor(tag: string) {
    this.tag = tag;
  }
}

function show(body: string) {
  let inTag = false;
  let out = [];
  let text = '';
  for (const char of body) {
    if (char === '<') {
      inTag = true;
      if (text) {
        out.push(new Text(text));
      }
      text = '';
    } else if (char === '>') {
      inTag = false;
      out.push(new Tag(text));
      text = '';
    } else {
      text += char;
    }
  }

  if (!inTag && text) {
    out.push(new Text(text));
  }

  let inBody = false;
  let bodyText = ''

  for (const token of out) {
    if (token instanceof Text) {
      if (inBody) {
        bodyText += token.text;
      }
    } else if (token.tag === 'body') {
      inBody = true;
    } else if (token.tag === '/body') {
      inBody = false;
    }
  }

  console.log(bodyText);
}

async function load(url: string) {
  const { headers, body } = await request(url);
  show(body);
}

function main() {
  const url = process.argv[2];
  load(url);
}

main();
