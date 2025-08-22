from django.http import JsonResponse

def aasa_view(request):
    return JsonResponse(
        {
            "applinks": {
                "details": [
                    {
                        "appID": "8MQV6MU23W.com.lexipark.app",
                        "paths": ["/analysis/*", "/users/profile/*", "/"]
                    }
                ]
            }
        }
    )
