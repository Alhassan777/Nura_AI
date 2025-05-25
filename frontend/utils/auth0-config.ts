// Auth0 configuration settings

interface Auth0Config {
  auth0Domain: string;
  clientId: string;
  clientSecret: string;
  baseUrl: string;
  secret: string;
}

export const getAuth0Config = (): Auth0Config => {
  const auth0Domain = process.env.AUTH0_DOMAIN;
  const clientId = process.env.AUTH0_CLIENT_ID;
  const clientSecret = process.env.AUTH0_CLIENT_SECRET;
  const baseUrl = process.env.AUTH0_BASE_URL;
  const secret = process.env.AUTH0_SECRET;
  
  if (!auth0Domain) {
    throw new Error('AUTH0_DOMAIN is not defined in environment variables');
  }
  
  if (!clientId) {
    throw new Error('AUTH0_CLIENT_ID is not defined in environment variables');
  }
  
  if (!clientSecret) {
    throw new Error('AUTH0_CLIENT_SECRET is not defined in environment variables');
  }
  
  if (!baseUrl) {
    throw new Error('AUTH0_BASE_URL is not defined in environment variables');
  }
  
  if (!secret) {
    throw new Error('AUTH0_SECRET is not defined in environment variables');
  }
  
  return {
    auth0Domain,
    clientId,
    clientSecret,
    baseUrl,
    secret,
  };
}; 