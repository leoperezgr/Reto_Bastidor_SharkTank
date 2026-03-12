using System;
using System.Collections;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;
using Newtonsoft.Json;

public class ApiClient : MonoBehaviour
{
    [SerializeField] private string baseUrl = "http://127.0.0.1:8000";

    private const string START_SESSION_ENDPOINT = "/api/session/start";
    private const string NEXT_TURN_ENDPOINT = "/api/session/next-turn";

    public void StartSession(StartSessionRequest requestData, Action<SessionTurnResponse> onSuccess, Action<string> onError)
    {
        StartCoroutine(SendPostRequest(START_SESSION_ENDPOINT, requestData, onSuccess, onError));
    }

    public void NextTurn(NextTurnRequest requestData, Action<SessionTurnResponse> onSuccess, Action<string> onError)
    {
        if (string.IsNullOrEmpty(requestData.session_id))
        {
            onError?.Invoke("Session ID is required for next turn.");
            return;
        }

        StartCoroutine(SendPostRequest(NEXT_TURN_ENDPOINT, requestData, onSuccess, onError));
    }

    private IEnumerator SendPostRequest<TRequest>(
        string endpoint,
        TRequest requestData,
        Action<SessionTurnResponse> onSuccess,
        Action<string> onError)
    {
        string url = baseUrl + endpoint;
        string jsonData = JsonConvert.SerializeObject(requestData);

        Debug.Log($"POST {url}");
        Debug.Log($"Request JSON: {jsonData}");

        using (UnityWebRequest request = new UnityWebRequest(url, UnityWebRequest.kHttpVerbPOST))
        {
            byte[] bodyRaw = Encoding.UTF8.GetBytes(jsonData);
            request.uploadHandler = new UploadHandlerRaw(bodyRaw);
            request.downloadHandler = new DownloadHandlerBuffer();
            request.SetRequestHeader("Content-Type", "application/json");

            yield return request.SendWebRequest();

            string responseText = request.downloadHandler != null
                ? request.downloadHandler.text
                : "";

            Debug.Log($"Response Status: {(long)request.responseCode}");
            Debug.Log($"Response Body: {responseText}");

            if (request.result != UnityWebRequest.Result.Success)
            {
                string errorMsg =
                    $"HTTP Error: {request.error}\n" +
                    $"Status Code: {(long)request.responseCode}\n" +
                    $"Response Body: {responseText}";
                Debug.LogError(errorMsg);
                onError?.Invoke(errorMsg);
                yield break;
            }

            try
            {
                SessionTurnResponse response =
                    JsonConvert.DeserializeObject<SessionTurnResponse>(responseText);

                if (response == null)
                {
                    onError?.Invoke("Response parsed as null.");
                    yield break;
                }

                onSuccess?.Invoke(response);
            }
            catch (Exception e)
            {
                string parseError =
                    $"Failed to parse response: {e.Message}\n" +
                    $"Raw Response: {responseText}";
                Debug.LogError(parseError);
                onError?.Invoke(parseError);
            }
        }
    }
}