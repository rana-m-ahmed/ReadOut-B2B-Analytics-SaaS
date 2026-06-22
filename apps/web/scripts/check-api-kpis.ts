import { createClient } from '@supabase/supabase-js';
import * as dotenv from 'dotenv';
import { resolve } from 'path';

// Load env vars
dotenv.config({ path: resolve(__dirname, '../.env') });

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

const supabase = createClient(supabaseUrl, supabaseAnonKey);

async function run() {
  console.log("Signing in anonymously...");
  const { data: authData, error: authErr } = await supabase.auth.signInAnonymously();
  if (authErr) throw authErr;
  
  const token = authData.session?.access_token;
  console.log("Token acquired.");

  console.log("Fetching datasets...");
  const headers = {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  };
  
  const dsResp = await fetch('http://localhost:8000/datasets', { headers });
  const datasets = await dsResp.json();
  
  const demoDs = datasets.find((d: any) => d.name.toLowerCase().includes('demo')) || datasets[0];
  if (!demoDs) {
    console.error("No dataset found!");
    return;
  }
  
  console.log(`Using dataset: ${demoDs.id} (${demoDs.name})`);

  const questions = [
    "total revenue this period",
    "total orders this period",
    "average order value",
  ];

  for (const q of questions) {
    console.log(`\nAsking: "${q}"...`);
    const t0 = Date.now();
    const askResp = await fetch('http://localhost:8000/ask', {
      method: 'POST',
      headers,
      body: JSON.stringify({
        dataset_id: demoDs.id,
        question: q,
        session_id: null
      })
    });
    
    if (!askResp.ok) {
      console.error(`Error ${askResp.status}:`, await askResp.text());
      continue;
    }
    
    const data = await askResp.json();
    console.log(`Time: ${Date.now() - t0}ms`);
    if (data.clarification_required) {
      console.log(`-> Clarification Required: ${data.clarification_required.message}`);
    } else {
      const chart = data.chart;
      if (chart && chart.data && chart.data.length > 0) {
        const yKey = chart.y_keys?.[0] || 'value';
        const val = chart.data[0][yKey];
        console.log(`-> ${yKey}: ${val}`);
        if (chart.data[0].delta_percent) {
          console.log(`-> Delta: ${(chart.data[0].delta_percent * 100).toFixed(1)}%`);
        }
      } else {
        console.log("-> No chart data returned");
      }
    }
  }
}

run().catch(console.error);
