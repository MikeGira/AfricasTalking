import 'dotenv/config'; // This loads the .env file immediately upon import
import africaTalking from 'africastalking';

// Debugging: Verify variables are loaded before initializing the SDK
console.log("Environment Check:");
console.log("- AT_USERNAME:", process.env.AT_USERNAME);

const atFn = africaTalking.default || africaTalking;

const client = atFn({
    username: process.env.AT_USERNAME,
    apiKey: process.env.AT_API_KEY
});

client.SMS.send({
    to: '+250788285524',
    message: 'M2R763TWEF \nConfirmed. You have received a payment of RWF 1000.00 from +250788285524 on 2024-06-17 at 12:00:00. Your new balance is RWF 5000.00.',
    from: 'M-MONEY'
})
.then(res => console.log('Success:', JSON.stringify(res, null, 2)))
.catch(err => console.error('Error details:', err));