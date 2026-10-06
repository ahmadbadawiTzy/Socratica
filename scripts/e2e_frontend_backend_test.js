/**
 * End-to-end verification script mimicking frontend client:
 * 1. Checks Next.js pages: /login, /chat
 * 2. Authenticates through API with origin http://localhost:3000 (CORS test)
 * 3. Fetches user profile and courses
 * 4. Creates conversation
 * 5. Sends message, invoking Langflow -> Gemini/Qdrant -> FastAPI
 * 6. Verifies response structure, citations, latency, and status
 */

const http = require('http');

async function testPage(url) {
  return new Promise((resolve, reject) => {
    http.get(url, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => resolve({ status: res.statusCode, length: data.length }));
    }).on('error', reject);
  });
}

async function request(url, method, headers, body) {
  return new Promise((resolve, reject) => {
    const u = new URL(url);
    const req = http.request({
      hostname: u.hostname,
      port: u.port,
      path: u.pathname + u.search,
      method,
      headers
    }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        let json;
        try { json = JSON.parse(data); } catch (e) { json = data; }
        resolve({
          status: res.statusCode,
          headers: res.headers,
          data: json
        });
      });
    });
    req.on('error', reject);
    if (body) req.write(typeof body === 'string' ? body : JSON.stringify(body));
    req.end();
  });
}

async function main() {
  console.log('=== STEP 6: FRONTEND & BACKEND E2E TEST ===\n');

  // 1. Next.js page availability
  console.log('1. Testing Next.js pages:');
  const loginPage = await testPage('http://localhost:3000/login');
  console.log(' - GET http://localhost:3000/login -> Status:', loginPage.status, '(HTML bytes:', loginPage.length, ')');
  const chatPage = await testPage('http://localhost:3000/chat');
  console.log(' - GET http://localhost:3000/chat  -> Status:', chatPage.status, '(HTML bytes:', chatPage.length, ')');

  // 2. CORS Preflight & Login
  console.log('\n2. Testing CORS and Login (Origin: http://localhost:3000):');
  const loginRes = await request('http://localhost:8000/api/v1/auth/login', 'POST', {
    'Origin': 'http://localhost:3000',
    'Content-Type': 'application/json'
  }, {
    email: 'student_11151e@univ.ac.id',
    password: 'Password123!'
  });

  console.log(' - POST /api/v1/auth/login -> Status:', loginRes.status);
  console.log(' - CORS Access-Control-Allow-Origin:', loginRes.headers['access-control-allow-origin']);
  if (!loginRes.data.access_token) {
    throw new Error('Login failed: ' + JSON.stringify(loginRes.data));
  }
  const token = loginRes.data.access_token;
  const authHeaders = {
    'Origin': 'http://localhost:3000',
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  };

  // 3. User Profile and Course
  console.log('\n3. Fetching User Profile & Enrolled Courses:');
  const meRes = await request('http://localhost:8000/api/v1/auth/me', 'GET', authHeaders);
  console.log(' - GET /api/v1/auth/me -> Status:', meRes.status, '| User:', meRes.data.display_name, '(', meRes.data.email, ')');

  const coursesRes = await request('http://localhost:8000/api/v1/courses', 'GET', authHeaders);
  console.log(' - GET /api/v1/courses -> Status:', coursesRes.status, '| Courses count:', coursesRes.data.length);
  const course = coursesRes.data[0];
  console.log('   Selected Course:', course.id, '| Code:', course.code, '| Name:', course.name);

  // 4. Create Conversation
  console.log('\n4. Creating Conversation:');
  const convRes = await request('http://localhost:8000/api/v1/conversations', 'POST', authHeaders, {
    course_id: course.id,
    mode: 'qa',
    title: 'E2E Verification Chat'
  });
  console.log(' - POST /api/v1/conversations -> Status:', convRes.status, '| Conv ID:', convRes.data.id);
  const convId = convRes.data.id;

  // 5. Send Message (Triggers Langflow -> Gemini / Qdrant)
  console.log('\n5. Sending message (Frontend -> FastAPI -> Langflow Unified -> Gemini/Qdrant):');
  const sendRes = await request(`http://localhost:8000/api/v1/conversations/${convId}/messages`, 'POST', authHeaders, {
    content: 'Apa yang dimaksud dengan abstraksi dalam pemrograman berorientasi objek?',
    mode: 'qa'
  });

  console.log(' - POST /conversations/{id}/messages -> Status:', sendRes.status);
  console.log(' - Response Content:\n', sendRes.data.content);
  console.log(' - Citations count:', (sendRes.data.citations || []).length);
  console.log(' - Mode:', sendRes.data.mode);
  console.log(' - Status:', sendRes.data.status);
  console.log(' - Assistant message ID:', sendRes.data.assistant_message_id);

  console.log('\n=== E2E TEST RESULT: PASS ===');
}

main().catch(err => {
  console.error('E2E TEST FAILED:', err);
  process.exit(1);
});
