# lambda/index.py

import json
import os
import urllib.request
import urllib.error

# FastAPI のベース URL を環境変数から取得
FASTAPI_BASE_URL = "https://eae5-34-44-125-155.ngrok-free.app"  
def lambda_handler(event, context):
    try:
        # リクエストボディを JSON としてパース
        body = json.loads(event.get("body", "{}"))
        prompt         = body["prompt"]                 
        max_new_tokens = body.get("max_new_tokens", 512)
        do_sample      = body.get("do_sample", True)
        temperature    = body.get("temperature", 0.7)
        top_p          = body["top_p"]                  

        # FastAPI /generate エンドポイントに渡すペイロードを組み立て
        payload = {
            "prompt": prompt,
            "max_new_tokens": max_new_tokens,
            "do_sample": do_sample,
            "temperature": temperature,
            "top_p": top_p
        }
        data = json.dumps(payload).encode("utf-8")

        # HTTP POST リクエストを作成
        url = f"{FASTAPI_BASE_URL}/generate"
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        # FastAPI を呼び出し
        with urllib.request.urlopen(req) as resp:
            status_code = resp.getcode()
            resp_body   = resp.read().decode("utf-8")

        # レスポンス JSON をパース
        result = json.loads(resp_body)

        # 成功レスポンス例:
        # {
        #   "generated_text": "string",
        #   "response_time": 0
        # }
        if "generated_text" not in result:
            raise Exception("Missing 'generated_text' in response")

        # 正常系レスポンスを返却
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type":                "application/json",
                "Access-Control-Allow-Origin":  "*",
                "Access-Control-Allow-Headers":"Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods":"OPTIONS,POST"
            },
            "body": json.dumps({
                "success":         True,
                "generated_text":  result["generated_text"],
                "response_time":   result.get("response_time")
            })
        }

    except KeyError as e:
        # クライアント側のパラメータ不足
        return {
            "statusCode": 400,
            "headers": {
                "Content-Type":                "application/json",
                "Access-Control-Allow-Origin":  "*"
            },
            "body": json.dumps({
                "success": False,
                "error":   f"Missing parameter: {e.args[0]}"
            })
        }

    except urllib.error.HTTPError as e:
        # FastAPI 側から 422 (Validation Error) やその他の HTTP エラーが返ってきた場合
        error_body = e.read().decode("utf-8")
        parsed = None
        try:
            parsed = json.loads(error_body)
        except json.JSONDecodeError:
            parsed = error_body

        return {
            "statusCode": e.code,
            "headers": {
                "Content-Type":                "application/json",
                "Access-Control-Allow-Origin":  "*"
            },
            "body": json.dumps({
                "success": False,
                "error":   parsed
            })
        }

    except Exception as e:
        # それ以外の例外
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type":                "application/json",
                "Access-Control-Allow-Origin":  "*"
            },
            "body": json.dumps({
                "success": False,
                "error":   str(e)
            })
        }
