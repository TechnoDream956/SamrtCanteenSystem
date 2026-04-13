/**
 * B.U Eats — API Configuration
 *
 * HOW IT WORKS:
 *  - In local development  → points to http://127.0.0.1:5000
 *  - After Railway deploy  → replace RAILWAY_URL below with your Railway URL
 *    e.g. "https://bu-eats-production.up.railway.app"
 *
 * You only need to change ONE line here and everything else updates automatically.
 */

const RAILWAY_URL = "https://smartcanteensystem-1.onrender.com"; 

// Auto-select: use localhost:5001 if testing locally, otherwise use Render URL
const isLocal = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
const API = isLocal ? "http://127.0.0.1:5001" : RAILWAY_URL;

// Freeze to prevent accidental mutation anywhere
Object.freeze({ API });
