/**
 * Browser Diagnostic Script for Authentication Issues
 * 
 * Copy and paste this into your browser console to diagnose the auth problem
 */

console.log('=== AUTHENTICATION DIAGNOSTIC ===');

// 1. Check localStorage data
console.log('\n1. LOCALSTORAGE CHECK:');
const storedData = localStorage.getItem('auth.tokens.v1');
console.log('Raw stored data:', storedData ? 'EXISTS' : 'MISSING');

if (storedData) {
  try {
    const tokens = JSON.parse(storedData);
    console.log('Parsed tokens:', tokens);
    console.log('Access token exists:', !!tokens.access_token);
    console.log('Refresh token exists:', !!tokens.refresh_token);
    console.log('Token type:', tokens.token_type);
    console.log('Expires in:', tokens.expires_in, 'seconds');
  } catch (error) {
    console.error('ERROR: Cannot parse stored tokens:', error);
  }
} else {
  console.error('ERROR: No tokens found in localStorage');
}

// 2. Validate token format
console.log('\n2. TOKEN FORMAT VALIDATION:');
if (storedData) {
  try {
    const tokens = JSON.parse(storedData);
    if (tokens.access_token) {
      const parts = tokens.access_token.split('.');
      console.log('Token parts count:', parts.length, '(should be 3)');
      
      if (parts.length === 3) {
        console.log('✅ Token format is valid');
        
        // Decode and show payload
        try {
          const payload = JSON.parse(atob(parts[1] + '==='));
          console.log('Token payload:', payload);
          
          // Check expiration
          if (payload.exp) {
            const currentTime = Math.floor(Date.now() / 1000);
            const timeLeft = payload.exp - currentTime;
            console.log('Token expires in:', timeLeft, 'seconds');
            
            if (timeLeft <= 0) {
              console.error('❌ Token is EXPIRED');
            } else if (timeLeft < 300) { // Less than 5 minutes
              console.warn('⚠️ Token expires soon:', timeLeft, 'seconds');
            } else {
              console.log('✅ Token is valid for', Math.floor(timeLeft / 60), 'minutes');
            }
          }
        } catch (decodeError) {
          console.error('❌ Cannot decode token payload:', decodeError);
        }
      } else {
        console.error('❌ Token format is INVALID (should have 3 parts)');
      }
    }
  } catch (parseError) {
    console.error('❌ Cannot parse tokens:', parseError);
  }
}

// 3. Test API call
console.log('\n3. API CALL TEST:');
if (storedData) {
  try {
    const tokens = JSON.parse(storedData);
    if (tokens.access_token) {
      console.log('Making test request to /auth/me...');
      
      fetch('http://localhost:8000/auth/me', {
        headers: {
          'Authorization': `Bearer ${tokens.access_token}`,
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        }
      })
      .then(response => {
        console.log('Response status:', response.status);
        console.log('Response ok:', response.ok);
        
        if (response.ok) {
          return response.json();
        } else {
          return response.text().then(text => {
            console.log('Error response body:', text);
            throw new Error(`HTTP ${response.status}: ${text}`);
          });
        }
      })
      .then(data => {
        console.log('✅ API CALL SUCCESS!');
        console.log('User data:', data);
      })
      .catch(error => {
        console.error('❌ API CALL FAILED:', error.message);
      });
    } else {
      console.warn('⚠️ No access token to test with');
    }
  } catch (error) {
    console.error('❌ Error testing API:', error);
  }
} else {
  console.warn('⚠️ No tokens to test with');
}

// 4. Test different header formats
console.log('\n4. HEADER FORMAT TEST:');
if (storedData) {
  try {
    const tokens = JSON.parse(storedData);
    const token = tokens.access_token;
    
    const testCases = [
      { name: 'Bearer with space', header: `Bearer ${token}` },
      { name: 'Bearer no space', header: `Bearer${token}` },
      { name: 'Token only', header: token }
    ];
    
    testCases.forEach(testCase => {
      fetch('http://localhost:8000/auth/me', {
        headers: {
          'Authorization': testCase.header,
          'Content-Type': 'application/json'
        }
      })
      .then(response => {
        console.log(`${testCase.name}: ${response.status} ${response.ok ? '✅' : '❌'}`);
        if (!response.ok) {
          return response.text().then(text => console.log(`  Error: ${text.substring(0, 100)}...`));
        }
      })
      .catch(error => console.log(`${testCase.name}: ERROR - ${error.message}`));
    });
  } catch (error) {
    console.error('Error in header format test:', error);
  }
}

// 5. Recommendations
console.log('\n5. RECOMMENDATIONS:');
console.log('If tests show:');
console.log('❌ Token format invalid → Clear localStorage and re-login');
console.log('❌ Token expired → Wait for auto-refresh or re-login');
console.log('❌ API call 401 → Backend token validation issue');
console.log('❌ API call 403 → Account not activated (backend issue)');
console.log('✅ All tests pass → Issue might be in React component state');

// 6. Quick fixes
console.log('\n6. QUICK FIXES:');
console.log('To clear corrupted tokens:');
console.log('localStorage.removeItem("auth.tokens.v1")');
console.log('location.reload()');

console.log('\n=== DIAGNOSTIC COMPLETE ===');