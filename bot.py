import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()

# Estado do sistema
historico = []

sinal_atual = None
nivel = 0  # 0 = sinal inicial, 1 = Gale 1, 2 = Gale 2

greens_seguidas = 0
total_greens = 0
total_losses = 0


def calcular_sinal():
    """
    Escolhe a cor com maior frequência no histórico.
    Isto é apenas uma heurística estatística e não prevê
    o resultado seguinte.
    """

    if not historico:
        return "azul"

    azuis = historico.count("azul")
    vermelhos = historico.count("vermelho")

    if azuis > vermelhos:
        return "azul"

    if vermelhos > azuis:
        return "vermelho"

    # Em caso de empate estatístico
    return "azul"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎲 BAC BO SIGNALS PT\n\n"
        "🟢 Bot online!\n\n"
        "Comandos:\n"
        "/sinal - Novo sinal\n"
        "/resultado azul\n"
        "/resultado vermelho\n"
        "/resultado empate\n"
        "/historico - Ver histórico\n"
        "/estatisticas - Ver estatísticas"
    )


async def sinal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global sinal_atual, nivel

    if sinal_atual is None:
        sinal_atual = calcular_sinal()
        nivel = 0

        cor = "🔵 AZUL" if sinal_atual == "azul" else "🔴 VERMELHO"

        await update.message.reply_text(
            f"{cor}\n"
            "🛡️ PROTEGE EMPATE\n\n"
            f"🔥 GREENS SEGUIDAS: {greens_seguidas}"
        )
    else:
        await update.message.reply_text(
            "⚠️ Já existe um sinal em andamento.\n"
            "Aguarda o resultado desta ronda."
        )


async def resultado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global sinal_atual
    global nivel
    global greens_seguidas
    global total_greens
    global total_losses

    if not context.args:
        await update.message.reply_text(
            "Utilização:\n"
            "/resultado azul\n"
            "/resultado vermelho\n"
            "/resultado empate"
        )
        return

    resultado_recebido = context.args[0].lower().strip()

    if resultado_recebido not in ["azul", "vermelho", "empate"]:
        await update.message.reply_text(
            "❌ Resultado inválido.\n\n"
            "Usa:\n"
            "/resultado azul\n"
            "/resultado vermelho\n"
            "/resultado empate"
        )
        return

    historico.append(resultado_recebido)

    if sinal_atual is None:
        await update.message.reply_text(
            "📊 Resultado registado.\n\n"
            "Ainda não existe um sinal ativo.\n"
            "Usa /sinal para iniciar."
        )
        return

    # Empate protegido = GREEN
    if resultado_recebido == "empate":
        greens_seguidas += 1
        total_greens += 1

        sinal_atual = None
        nivel = 0

        await update.message.reply_text(
            "🟢 GREEN\n"
            "🟡 EMPATE PROTEGIDO\n\n"
            f"🔥 GREENS SEGUIDAS: {greens_seguidas}"
        )
        return

    # Resultado igual ao sinal = GREEN
    if resultado_recebido == sinal_atual:
        greens_seguidas += 1
        total_greens += 1

        sinal_atual = None
        nivel = 0

        await update.message.reply_text(
            "🟢 GREEN\n\n"
            f"🔥 GREENS SEGUIDAS: {greens_seguidas}"
        )
        return

    # Resultado contrário
    if nivel == 0:
        nivel = 1

        await update.message.reply_text(
            "⚠️ GALE 1"
        )
        return

    if nivel == 1:
        nivel = 2

        await update.message.reply_text(
            "⚠️ GALE 2"
        )
        return

    # Perdeu sinal + Gale 1 + Gale 2
    total_losses += 1
    greens_seguidas = 0

    sinal_atual = None
    nivel = 0

    await update.message.reply_text(
        "🛑 NÃO FOI DESTA\n"
        "⏳ ESPERA PELA PRÓXIMA"
    )


async def historico_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not historico:
        await update.message.reply_text(
            "📊 Ainda não existem resultados registados."
        )
        return

    ultimos = historico[-20:]

    texto = "📊 ÚLTIMOS RESULTADOS\n\n"

    for i, resultado_item in enumerate(ultimos, 1):
        if resultado_item == "azul":
            emoji = "🔵"
        elif resultado_item == "vermelho":
            emoji = "🔴"
        else:
            emoji = "🟡"

        texto += f"{i}. {emoji} {resultado_item.upper()}\n"

    await update.message.reply_text(texto)


async def estatisticas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total = len(historico)

    azuis = historico.count("azul")
    vermelhos = historico.count("vermelho")
    empates = historico.count("empate")

    await update.message.reply_text(
        "📊 ESTATÍSTICAS\n\n"
        f"🎲 Resultados: {total}\n"
        f"🔵 Azul: {azuis}\n"
        f"🔴 Vermelho: {vermelhos}\n"
        f"🟡 Empates: {empates}\n\n"
        f"🟢 Total Greens: {total_greens}\n"
        f"🔴 Total Losses: {total_losses}\n"
        f"🔥 Greens seguidas: {greens_seguidas}"
    )


def main():
    if not TOKEN:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN não está configurado."
        )

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("sinal", sinal))
    app.add_handler(CommandHandler("resultado", resultado))
    app.add_handler(CommandHandler("historico", historico_cmd))
    app.add_handler(CommandHandler("estatisticas", estatisticas))

    logging.info("Bac Bo Signals PT iniciado.")

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
