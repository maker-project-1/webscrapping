

	//サブカテゴリ一覧共通サブミット(formのactionを変更する。下位階層に遷移する為)
	function fnSubCategorySubmit(form, path) {
		if(form == "" || path == ""){
			return false;
		}
		document.forms[form].action = path;
		document.forms[form].submit();
	}

	//フィルタ用サブミット(namexのhidden値にvalue入れる)
	function fnFilterSubmit(form, namex, value) {
		if(namex != ""){
			document.forms[form][namex].value = value;
		}
		document.forms[form].submit();
	}

	//検索フィルタ部クリア(１項目毎)
	function fnFilterSubmitClr(form_name,namex){
		var elems = form_name.elements;
		for(i = 0; i < elems.length; i++){
			elem = elems[i];
			
			if(elem.name == namex){
				// テキストクリア
				if(elem.type == "text"){
				  elem.value = "";
				  form_name.submit();
				}
				// hiddenクリア
				if(elem.type == "hidden"){
				  elem.value = "";
				  form_name.submit();
				}
				// チェックボックスクリア
				if(elem.type == "checkbox"){
				  elem.checked  = false;
				  form_name.submit();
				}
			}
		}
	}


	//価格ボタン用サブミット(テキストボックスのminとmaxをコロンで結合してhiddenにセット)
	function fnBlockSubmitPrice(form, namex) {
		var min_price = "" ;
		var max_price = "" ;
		var price = "" ;
		min_price = document.forms[form]['min_price'].value ;
		max_price = document.forms[form]['max_price'].value ;
		price = min_price + "." + max_price;
		document.forms[form][namex].value = price;
		document.forms[form].submit();
	}

	//価格一覧行リンクサブミット(引数のminとmaxをコロンで結合してhiddenにセット)
	function fnBlockSubmitLinePrice(form, min_price,max_price) {
		var price = "" ;
		document.forms[form]['min_price'].value = min_price ;
		document.forms[form]['max_price'].value = max_price ;
		if(min_price != "" || max_price != ""){
			price = min_price + "." + max_price;
		}
		document.forms[form]['price'].value = price;
		document.forms[form].submit();
	}

	//ブロック共通サブミット
	function fnBlockSubmit(form, namex, val) {
		document.forms[form][namex].value = val;
		document.forms[form].submit();
	}

	//ブランドサブミット
	function fnBlockSubmitBrand(form, namex, val) {
		document.forms[form]["bsubmit.x"].value = "true";
		document.forms[form][namex].value = val;
		document.forms[form].submit();
	}

	//詳細検索
	function fnBlockSubmitLinePriceSearchDetails(form, path) {
		var min_price = "" ;
		var max_price = "" ;
		min_price = document.forms[form]['min_price'].value ;
		max_price = document.forms[form]['max_price'].value ;
		document.forms[form].action = path + "?min_price=" + min_price + "&max_price=" + max_price + "&search=t";
		document.forms[form].submit();

	}
