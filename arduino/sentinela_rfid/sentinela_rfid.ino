#include <SPI.h>
#include <MFRC522.h>
#include <WiFi.h>
#include <HTTPClient.h>

// Configurações da rede Wi-Fi
const char* ssid = "sua_rede_wifi";
const char* password = "sua_senha_wifi";

// URL do Servidor Flask
const char* serverUrl = "http://seu_ip:5000/api/leitores-rfid/bip";

// Identificação deste leitor
const char* codigoLeitor = "LEITOR-01";

// Mapeamento dos Pinos
#define SS_PIN           5
#define RST_PIN          22
#define BUZZER_PIN       4
#define LED_VERDE_PIN    17
#define LED_VERMELHO_PIN 16

MFRC522 rfid(SS_PIN, RST_PIN);

void setup() {
  Serial.begin(115200);

  SPI.begin();
  rfid.PCD_Init();

  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(LED_VERDE_PIN, OUTPUT);
  pinMode(LED_VERMELHO_PIN, OUTPUT);

  Serial.print("Conectando ao Wi-Fi");

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);

    Serial.print(".");

    digitalWrite(
      LED_VERMELHO_PIN,
      !digitalRead(LED_VERMELHO_PIN)
    );
  }

  digitalWrite(LED_VERMELHO_PIN, LOW);

  Serial.println("\nWi-Fi Conectado com sucesso!");

  Serial.print("IP do ESP32: ");
  Serial.println(WiFi.localIP());

  Serial.print("Leitor: ");
  Serial.println(codigoLeitor);

  tone(BUZZER_PIN, 1200, 80);
  delay(100);
  tone(BUZZER_PIN, 1500, 80);
}

void loop() {

  // Aguarda aproximação da tag
  if (!rfid.PICC_IsNewCardPresent() || !rfid.PICC_ReadCardSerial()) {
    return;
  }

  // Converte o UID para String Hexadecimal
  String uidString = "";

  for (byte i = 0; i < rfid.uid.size; i++) {
    if (rfid.uid.uidByte[i] < 0x10) {
      uidString += "0";
    }

    uidString += String(rfid.uid.uidByte[i], HEX);
  }

  uidString.toUpperCase();

  Serial.println("\n[RFID] Tag lida: " + uidString);
  Serial.print("[RFID] Leitor: ");
  Serial.println(codigoLeitor);

  // Verifica conexão Wi-Fi
  if (WiFi.status() == WL_CONNECTED) {

    HTTPClient http;

    http.begin(serverUrl);
    http.addHeader("Content-Type", "application/json");

    String jsonPayload =
      "{\"codigo_tag\":\"" + uidString +
      "\",\"codigo_leitor\":\"" + codigoLeitor + "\"}";

    Serial.println("[1] Iniciando HTTP...");
    Serial.println("[2] Enviando POST...");

    Serial.print("[JSON] ");
    Serial.println(jsonPayload);

    unsigned long inicio = millis();

    int httpResponseCode = http.POST(jsonPayload);

    unsigned long fim = millis();

    Serial.print("[2] POST terminou em: ");
    Serial.print(fim - inicio);
    Serial.println(" ms");

    Serial.print("[3] HTTP Code: ");
    Serial.println(httpResponseCode);

    if (httpResponseCode > 0) {

      String resposta = http.getString();

      Serial.println("[4] Resposta do servidor:");
      Serial.println("========== INICIO RESPOSTA ==========");
      Serial.println(resposta);
      Serial.println("=========== FIM RESPOSTA ===========");

      Serial.println();

      // Verifica se o campo existe na resposta
      if (resposta.indexOf("presenca_registrada") >= 0) {
        Serial.println("[TESTE] Campo presenca_registrada ENCONTRADO");
      } else {
        Serial.println("[TESTE] Campo presenca_registrada NAO ENCONTRADO");
      }

      // Verifica se existe true na resposta
      if (resposta.indexOf("true") >= 0) {
        Serial.println("[TESTE] TRUE ENCONTRADO");
      } else {
        Serial.println("[TESTE] TRUE NAO ENCONTRADO");
      }

      Serial.println();

      // VERDE somente se a presença realmente foi registrada
      if (
        httpResponseCode == 200 &&
        resposta.indexOf("presenca_registrada") >= 0 &&
        resposta.indexOf("true") >= 0
      ) {

        Serial.println("[LED] Presenca registrada -> VERDE");

        digitalWrite(LED_VERMELHO_PIN, LOW);
        digitalWrite(LED_VERDE_PIN, HIGH);

        tone(BUZZER_PIN, 2000, 150);

        delay(300);

        digitalWrite(LED_VERDE_PIN, LOW);

      } else {

        Serial.println("[LED] Presenca NAO registrada -> VERMELHO");

        digitalWrite(LED_VERDE_PIN, LOW);
        digitalWrite(LED_VERMELHO_PIN, HIGH);

        tone(BUZZER_PIN, 400, 400);

        delay(400);

        digitalWrite(LED_VERMELHO_PIN, LOW);
      }

    } else {

      Serial.print("[4] Erro HTTP: ");
      Serial.println(http.errorToString(httpResponseCode));

      Serial.println("[LED] Erro de comunicacao -> VERMELHO");

      digitalWrite(LED_VERDE_PIN, LOW);
      digitalWrite(LED_VERMELHO_PIN, HIGH);

      tone(BUZZER_PIN, 400, 400);

      delay(400);

      digitalWrite(LED_VERMELHO_PIN, LOW);
    }

    http.end();

  } else {

    Serial.println("Erro: ESP32 desconectado do Wi-Fi.");

    Serial.println("[LED] Wi-Fi desconectado -> VERMELHO");

    digitalWrite(LED_VERDE_PIN, LOW);
    digitalWrite(LED_VERMELHO_PIN, HIGH);

    tone(BUZZER_PIN, 400, 400);

    delay(400);

    digitalWrite(LED_VERMELHO_PIN, LOW);
  }

  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();

  Serial.println("=== FIM PROCESSAMENTO ===");

  delay(1200);
}