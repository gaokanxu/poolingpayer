from flask import Flask, request, jsonify
from solana.rpc.api import Client
from solana.transaction import Transaction, TransactionInstruction
from solana.keypair import Keypair
from solana.publickey import PublicKey
import base64
import hashlib
import time
import threading
import json

app = Flask(__name__)

# 初始化Solana客户端
client = Client("https://api.mainnet-beta.solana.com")

# 从文件中加载费用支付者的密钥对
def load_keypair_from_file(file_path):
    with open(file_path, 'r') as f:
        key_data = json.load(f)
    return Keypair.from_secret_key(bytes(key_data))

fee_payer = load_keypair_from_file('path/to/fee_payer_key.json')

# LumosCoin的Token Program ID
LUMOSCOIN_PROGRAM_ID = PublicKey("YourLumosCoinTokenProgramID")

# 存储已处理的请求ID和时间戳，防止重放攻击
processed_requests = {}
processed_requests_lock = threading.Lock()  # 线程安全锁

# 清理已处理请求的间隔时间（秒）
CLEANUP_INTERVAL = 3600  # 每小时清理一次
# 请求有效时间（毫秒）
REQUEST_TTL = 300000  # 请求5分钟内有效

def cleanup_processed_requests():
    """定期清理已处理的请求"""
    while True:
        current_time = time.time() * 1000  # 当前时间（毫秒）
        with processed_requests_lock:
            keys_to_delete = [key for key, timestamp in processed_requests.items() if current_time - timestamp > REQUEST_TTL]
            for key in keys_to_delete:
                del processed_requests[key]
        time.sleep(CLEANUP_INTERVAL)

# 启动清理线程
cleanup_thread = threading.Thread(target=cleanup_processed_requests)
cleanup_thread.daemon = True
cleanup_thread.start()

@app.route("/process-transaction", methods=["POST"])
def process_transaction():
    data = request.get_json()
    serialized_tx = data.get("transaction")
    request_id = data.get("requestId")
    timestamp = data.get("timestamp")
    transaction_hash = data.get("transactionHash")

    # 验证时间戳，确保请求在合理的时间范围内（如5分钟以内）
    if abs(time.time() * 1000 - timestamp) > REQUEST_TTL:
        return jsonify({"error": "Request expired"}), 403

    # 验证请求ID的唯一性，防止重放攻击
    with processed_requests_lock:
        if request_id in processed_requests:
            return jsonify({"error": "Duplicate request"}), 403
        processed_requests[request_id] = timestamp

    # 反序列化部分签署的交易
    serialized_tx_bytes = base64.b64decode(serialized_tx)
    transaction = Transaction.deserialize(serialized_tx_bytes)

    # 验证交易哈希
    server_transaction_hash = hashlib.sha256(serialized_tx_bytes).hexdigest()
    if server_transaction_hash != transaction_hash:
        return jsonify({"error": "Invalid transaction hash"}), 403

    # 验证交易类型和代币类型
    for instruction in transaction.instructions:
        if instruction.program_id != LUMOSCOIN_PROGRAM_ID:
            return jsonify({"error": "Invalid token program"}), 403

        # 检查是否为转账指令
        if not is_valid_transfer_instruction(instruction):
            return jsonify({"error": "Invalid transaction type"}), 403

    # 设置费用支付者
    transaction.fee_payer = fee_payer.public_key

    # 补充签名
    transaction.partial_sign(fee_payer)

    # 序列化和发送交易
    serialized_transaction = transaction.serialize()
    txid = client.send_raw_transaction(serialized_transaction)
    return jsonify({"transactionId": txid})

def is_valid_transfer_instruction(instruction):
    # 根据实际的LumosCoin转账指令结构进行判断
    TRANSFER_INSTRUCTION_ID = 1
    return instruction.data[0] == TRANSFER_INSTRUCTION_ID

if __name__ == "__main__":
    app.run(ssl_context=("path/to/your/cert.pem", "path/to/your/key.pem"))

