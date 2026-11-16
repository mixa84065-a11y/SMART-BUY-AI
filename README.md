# SMART BUY AI

Исходный проект Android-приложения SMART BUY AI (v0.5.2).

## Загрузка исходников с телефона

1. Загрузите в корень этого репозитория архив `SMART_BUY_AI_v0_5_2_GitHub_Source_SAFE.zip` из ChatGPT. Это архив исходников без приватного ключа подписи.
2. Откройте **Settings → Secrets and variables → Actions → New repository secret** и добавьте четыре секрета из личного архива **SMART_BUY_AI_Permanent_Signing_Kit.zip**:
   - `SMARTBUY_KEYSTORE_BASE64`
   - `SMARTBUY_KEYSTORE_PASSWORD`
   - `SMARTBUY_KEY_ALIAS`
   - `SMARTBUY_KEY_PASSWORD`
3. Откройте **Actions → Build SMART BUY AI Android APK → Run workflow**.
4. После завершения сборки скачайте артефакт `SMART-BUY-AI-v0.5.2-release`.

**Важно:** не загружайте `.jks`, Base64-ключ или пароли в репозиторий. Ключ подписи храните только в личном архиве и GitHub Secrets.

## Текущий статус

- Android application ID: `com.smartbuy.ai`
- Версия исходников: `0.5.2` (versionCode `12`)
- Android: Java 17, compileSdk 35
- Backend: FastAPI; тесты запускаются в CI
- Публичные API-ключи магазинов не требуются для сборки; живые цены появятся только после подключения разрешённых источников данных.
- APK ещё не собран и не проверен на устройстве. Совместимость подписи с ранее установленными сборками также пока не подтверждена.
