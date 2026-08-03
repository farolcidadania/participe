function popup(url, name, width, height, top) {
    return (window.open(url, name != "" ? "popup_" + name : "", "width=" + width + ", height=" + height + ", top=" + top + ", left=" + (((window.innerWidth - width) / 2) + window.screenX)));
}

function popup_pasta_digital(documento_tipo, documento, assinatura) {
    popup("https://www.cmf.sc.gov.br/softcam/popup/index.php?pagina=pasta_digital&documento_tipo=" + documento_tipo + "&documento=" + documento + (assinatura ? "&assinatura=1" : ""), "", 1200, 700, 50);
}
