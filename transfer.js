const { Transaction, SystemProgram, PublicKey, Keypair } = require('@solana/web3.js');
const fetch = require('node-fetch');
const crypto = require('crypto');
const { v4: uuidv4 } = require('uuid');

async function createAndSignTransaction(sender, recipient, amount, backendUrl, apiSecret) {
    // 初始化Solana连接
    const connection = new solanaWeb3.Connection(solanaWeb3.clusterApiUrl('mainnet-beta'), 'confirmed');

    // 获取最近的区块哈希
    const { blockhash } = await connection.getRecentBlockhash();

    // 创建交易对象
    const transaction = new Transaction().add(
        SystemProgram.transfer({
            fromPubkey: sender.publicKey,
            toPubkey: new solanaWeb3.PublicKey(recipient),
            lamports: amount,
        })
    );

    // 设置最近的区块哈希
    transaction.recentBlockhash = blockhash;

    // 部分签署交易
    transaction.partialSign(sender);

    // 序列化交易
    const serializedTransaction = transaction.serialize({ requireAllSignatures: false }).toString('base64');

    // 生成唯一标识符和时间戳
    const requestId = uuidv4();
    const timestamp = Date.now();

    // 生成交易哈希
    const transactionHash = crypto.createHash('sha256').update(serializedTransaction).digest('hex');

    // 发送到服务器
    const response = await fetch(`${backendUrl}/process-transaction`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            transaction: serializedTransaction,
            requestId: requestId,
            timestamp: timestamp,
            transactionHash: transactionHash
        }),
    });

    if (response.ok) {
        const data = await response.json();
        console.log('Transaction processed:', data);
    } else {
        console.error('Failed to process transaction:', response.status, response.statusText);
    }
}

// 示例用法
const sender = Keypair.fromSecretKey(new Uint8Array([/* sender secret key array */]));
const recipient = 'recipient public key';
const amount = 1000000; // 转账金额
const backendUrl = 'https://your-backend-service.com';

createAndSignTransaction(sender, recipient, amount, backendUrl).catch(console.error);

