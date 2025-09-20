#!/usr/bin/env python3
import asyncio
import websockets
import json

async def test_simulation():
    uri = "ws://localhost:8001/ws"

    # Estado de simulação BD padrão
    state = {
        "plan_type": "BD",
        "age": 30,
        "gender": "M",
        "retirement_age": 65,
        "monthly_salary": 8000,
        "target_benefit": 5000,
        "contribution_rate": 8.0,
        "discount_rate": 5.0,
        "admin_fee_rate": 1.0,
        "loading_fee_rate": 0.0,
        "salary_growth_real": 2.0,
        "mortality_table": "BR_EMS_2021",
        "smoothing_factor": 0.0,
        "benefit_mode": "fixed_value",
        "payment_timing": "due",
        "salary_months_per_year": 13,
        "benefit_months_per_year": 13,
        "initial_balance": 0
    }

    try:
        async with websockets.connect(uri) as websocket:
            print("Conectado ao WebSocket")

            # Enviar comando de simulação
            command = {
                "action": "simulate",
                "data": state
            }

            await websocket.send(json.dumps(command))
            print("Comando enviado")

            # Receber resposta
            response = await websocket.recv()
            print("Resposta recebida")

            # Parse da resposta (apenas os primeiros caracteres por enquanto)
            data = json.loads(response)
            print(f"Status: {data.get('status')}")
            if 'error' in data:
                print(f"Erro: {data['error']}")

    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    asyncio.run(test_simulation())