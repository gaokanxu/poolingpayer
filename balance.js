const { Connection, PublicKey } = require('@solana/web3.js');
const { getAssociatedTokenAddress, getAccount } = require('@solana/spl-token');
const tokenMintAddress = '3kEAACEgfQL44im4SZoshP38jfv3c4uKomryuHHa1sy4';

async function getTokenBalance(walletAddress, tokenMintAddress) {
    // 连接到Solana网
    //const connection = new Connection('https://api.devnet.solana.com', 'confirmed');
    const connection = new Connection('https://api.devnet.solana.com', 'confirmed');

    // 钱包地址和Token Mint地址
    const walletPublicKey = new PublicKey(walletAddress);
    const tokenMintPublicKey = new PublicKey(tokenMintAddress);

    // 获取关联的Token账户地址
    const tokenAccountAddress = await getAssociatedTokenAddress(tokenMintPublicKey, walletPublicKey);
    
    // 查询Token账户信息
    const tokenAccount = await getAccount(connection, tokenAccountAddress);

    // 将余额转换为真实的代币数量（考虑九位小数点）
    const decimals = BigInt(9); // 代币的小数位数
    const divisor = BigInt(Math.pow(10, Number(decimals))); // 将number转换为BigInt
    const tokenBalance = tokenAccount.amount / divisor;

    console.log(`${walletAddress}\nbalance: ${tokenBalance.toString()} Lumos Coins`);

    return tokenAccount.amount;
}

// 示例用法

const walletAddress = 'GtqFfeXnfmoxbexjoVcr758taRmjrWHg8jnVWeLjdYnU';
getTokenBalance(walletAddress, tokenMintAddress).catch(console.error);


