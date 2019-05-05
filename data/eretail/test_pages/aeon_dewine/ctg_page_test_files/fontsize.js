(function($){

	$(function(){
		fontsizeChange();
	});

	function fontsizeChange(){

		var changeArea = $("#container");			//フォントサイズ変更エリア
		var btnArea = $("#fontSize");				//フォントサイズ変更ボタンエリア
		var changeBtn = btnArea.find(".changeBtn");	//フォントサイズ変更ボタン
		var fontSize = [90,100,120];				//フォントサイズ（HTMLと同じ並び順、幾つでもOK、単位は％）
		var ovStr = "_ov";							//ロールオーバー画像ファイル末尾追加文字列（ロールオーバー画像を使用しない場合は値を空にする）
		var activeClass = "active";					//フォントサイズ変更ボタンのアクティブ時のクラス名
		var defaultSize = 2;						//初期フォントサイズ設定（HTMLと同じ並び順で0から数値を設定）
		var cookieExpires = 7;						//クッキー保存期間
		var sizeLen = fontSize.length;
		var useImg = ovStr!="" && changeBtn.is("[src]");

		//現在クッキー確認関数
		function nowCookie(){
			return $.cookie("fontsize");
		}

		//画像切替関数
		function imgChange(elm1,elm2,str1,str2){
			elm1.attr("src",elm2.attr("src").replace(new RegExp("^(\.+)"+str1+"(\\.[a-z]+)$"),"$1"+str2+"$2"));
		}

		//マウスアウト関数
		function mouseOut(){
			for(var i=0; i<sizeLen; i++){
				if(nowCookie()!=fontSize[i]){
					imgChange(changeBtn.eq(i),changeBtn.eq(i),ovStr,"");
				}
			}
		}

		//フォントサイズ設定関数
		function sizeChange(){
			changeArea.css({fontSize:nowCookie()+"%"});
      var size = nowCookie();
      if (size==90) $('').css('height', '3em');
      else if (size==100) $('').css('height', '2.8em');
      else if (size==120) $('').css('height', '2.34em');
		}

		//クッキー設定関数
		function cookieSet(index){
			$.cookie("fontsize",fontSize[index],{path:'/',expires:cookieExpires});
		}

		//初期表示
		if(nowCookie()){
			for(var i=0; i<sizeLen; i++){
				if(nowCookie()==fontSize[i]){
					sizeChange();
					var elm = changeBtn.eq(i);
					if(useImg){
						imgChange(elm,elm,"",ovStr);
					}
					elm.addClass(activeClass);
					break;
				}
			}
		}
		else {
			cookieSet(defaultSize);
			sizeChange();
			var elm = changeBtn.eq(defaultSize);
			if(useImg){
				imgChange(elm,elm,"",ovStr);
				imgChange($("<img>"),elm,"",ovStr);
			}
			elm.addClass(activeClass);
		}

		//ホバーイベント（画像タイプ）
		if(useImg){
			changeBtn.each(function(i){
				var self = $(this);
				self.hover(
				function(){
					if(nowCookie()!=fontSize[i]){
						imgChange(self,self,"",ovStr);
					}
				},
				function(){
					mouseOut();
				});
			});
		}

		//クリックイベント
		changeBtn.click(function(){
			var index = changeBtn.index(this);
			var self = $(this);
			cookieSet(index);
			sizeChange();
			if(useImg){
				mouseOut();
			}
			if(!self.hasClass(activeClass)){
				changeBtn.not(this).removeClass(activeClass);
				self.addClass(activeClass);
			}
		});

	}

})(jQuery);
