from flask import Flask, request, jsonify, send_from_directory
import requests
import grpc
import euromil_pb2
import euromil_pb2_grpc

app = Flask(__name__)

# Configurações para os serviços externos
CREDIBANK_URL = "http://localhost:8080"
EUROMIL_SERVER = "localhost:50051"

# Função para criar o cheque digital usando o serviço CrediBank
def generate_digital_check(credit_account_id, value):
    try:
        response = requests.get(f"{CREDIBANK_URL}/check/{credit_account_id}/ammount/{value}/")
        response.raise_for_status()
        return response.json()[0]  # Retorna o primeiro item da lista com os detalhes do cheque
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

# Função para registar a aposta no serviço EuromilRegister
def register_euromil_bet(key, check_id):
    try:
        with grpc.insecure_channel(EUROMIL_SERVER) as channel:
            stub = euromil_pb2_grpc.EuromilStub(channel)
            response = stub.RegisterEuroMil(euromil_pb2.RegisterRequest(key=key, checkid=check_id))
            return response.message
    except Exception as e:
        return f"Error registering bet: {e}"

# Endpoint para registar uma aposta
@app.route('/register_bet', methods=['POST'])
def register_bet():
    # Obtém os dados enviados pelo utilizador
    data = request.json
    key = data.get("key")
    credit_account_id = data.get("credit_account_id")

    # Valida os dados
    if not key or not credit_account_id:
        return jsonify({"error": "Missing key or credit account ID"}), 400
    if len(credit_account_id) != 16 or not credit_account_id.isdigit():
        return jsonify({"error": "Invalid credit account ID. It must be a 16-digit number."}), 400

    # Cria o cheque digital
    check_response = generate_digital_check(credit_account_id, 10)
    if "error" in check_response:
        return jsonify({"error": f"CrediBank error: {check_response['error']}"}), 500

    check_id = check_response.get("checkID")

    # Regista a aposta
    registration_response = register_euromil_bet(key, check_id)
    if "Error" in registration_response:
        return jsonify({"error": registration_response}), 500

    return jsonify({"message": "Bet successfully registered!", "details": registration_response})

@app.route("/", methods=["GET"])
def serve_frontend():
    return send_from_directory(app.static_folder, "frontend/index.html")

# Inicializa o servidor Flask
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5005)
