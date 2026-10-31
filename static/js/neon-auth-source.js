import {createAuthClient} from '@neon/auth';
const root=document.getElementById('managed-auth');
const client=createAuthClient(root.dataset.url);
const status=document.getElementById('auth-status');
const form=document.getElementById('managed-auth-form');
async function refresh(){const {data,error}=await client.getSession();if(error) throw error;status.textContent=data?.user ? `Signed in as ${data.user.email}` : 'You are signed out.';}
form.addEventListener('submit',async event=>{event.preventDefault();const button=event.submitter;button.disabled=true;status.textContent='Please wait…';try{const values=Object.fromEntries(new FormData(form));const result=button.value==='signup'?await client.signUp.email({email:values.email,password:values.password,name:values.name}):await client.signIn.email({email:values.email,password:values.password});if(result.error)throw result.error;form.reset();await refresh();}catch(error){status.textContent=error.message||'Authentication failed. Please try again.';}finally{button.disabled=false;}});
document.getElementById('managed-signout').addEventListener('click',async()=>{try{await client.signOut();await refresh();}catch{status.textContent='Unable to sign out. Please retry.';}});
refresh().catch(()=>{status.textContent='Unable to restore your session. Please retry.';});
