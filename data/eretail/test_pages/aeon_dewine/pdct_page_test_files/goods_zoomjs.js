jQuery(function() {
	if (!(jQuery.browser.msie && jQuery.browser.version <= 6)){
		jQuery('#gallery a.info').bigPicture({
			'infoLabel': '画像コメントを表示する',
			'infoHideLabel': '画像コメントを隠す',
			'hideLabel': '閉じる',
			'boxEaseSpeed': 500,
			'enableInfo': true,
			'infoPosition': 'top'
		});
	}
	else{
		jQuery(".goodsimg_  a").removeClass("info");
		jQuery(".goodsimg_  a").attr({target:"_blank"});
		jQuery(".etc_goodsimg_ a").removeClass("info");
		jQuery(".etc_goodsimg_ a").attr({target:"_blank"});
	}
});