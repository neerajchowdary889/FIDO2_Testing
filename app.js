const express = require("express");
const bodyParser = require("body-parser");
const crypto = require("crypto");
const cors = require("cors"); // Import the cors package
const app = express();

// In-memory database for demo purposes
const users = {};

app.use(bodyParser.json());
app.use(cors()); // Enable CORS for all routes

// Utility function to generate a random challenge
function generateChallenge() {
  return crypto.randomBytes(32).toString("base64url");
}

// Endpoint: Start the registration process
app.post("/register/start", (req, res) => {
  const { username } = req.body;
  if (!username) {
    return res.status(400).send({ error: "Username is required" });
  }

  const challenge = generateChallenge();
  users[username] = { challenge }; // Store challenge temporarily

  const publicKeyCredentialCreationOptions = {
    challenge: Buffer.from(challenge, "base64url"),
    rp: {
      name: "Demo Site",
      id: "localhost",
    },
    user: {
      id: Buffer.from(crypto.randomBytes(16)),
      name: username,
      displayName: username,
    },
    pubKeyCredParams: [{ type: "public-key", alg: -7 }],
    authenticatorSelection: {
      userVerification: "discouraged",
    },
    timeout: 60000,
    attestation: "direct",
  };

  res.send(publicKeyCredentialCreationOptions);
});

// Endpoint: Complete the registration process
app.post("/register/complete", (req, res) => {
  const { username, credential } = req.body;
  const user = users[username];

  if (!user) {
    return res.status(400).send({ error: "User not found" });
  }

  // Basic check that the credential object exists
  if (!credential || !credential.id || !credential.response) {
    return res.status(400).send({ error: "Invalid credential" });
  }

  // Minimal verification placeholder
  // For production, parse and validate 'credential.response.clientDataJSON' and 'attestationObject'
  // using a trusted library like 'fido2-lib'.
  if (!credential.response.attestationObject) {
    return res.status(400).send({ error: "Missing attestation object" });
  }

  // Store credential in memory (for demo purposes)
  users[username] = {
    ...user,
    credentialId: credential.id,
    publicKey: credential.response.attestationObject,
  };

  res.send({ success: true });
});

app.listen(3000, () => {
  console.log("Server running on http://localhost:3000");
});