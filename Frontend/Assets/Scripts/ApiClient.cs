using System;
using System.Collections;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;

public class ApiClient : MonoBehaviour
{
    [SerializeField] private string baseUrl = "http://localhost:8000"; // Configurable from Inspector

    private const string START_SESSION_ENDPOINT = "/api/session/start";
    private const string NEXT_TURN_ENDPOINT = "/api/session/next-turn";

    // Start a new session
    public void StartSession(StartSessionRequest request, Action<SessionTurnResponse> onSuccess, Action<string> onError)
    {
        StartCoroutine(SendPostRequest(START_SESSION_ENDPOINT, JsonUtility.ToJson(request), onSuccess, onError));
    }

    // Send next turn with user message
    public void NextTurn(NextTurnRequest request, Action<SessionTurnResponse> onSuccess, Action<string> onError)
    {
        if (string.IsNullOrEmpty(request.session_id))
        {
            onError?.Invoke("Session ID is required for next turn.");
            return;
        }
        StartCoroutine(SendPostRequest(NEXT_TURN_ENDPOINT, JsonUtility.ToJson(request), onSuccess, onError));
    }

    private IEnumerator SendPostRequest(string endpoint, string jsonData, Action<SessionTurnResponse> onSuccess, Action<string> onError)
    {
        string url = baseUrl + endpoint;
        Debug.Log($"Sending POST to {url} with data: {jsonData}");

        using (UnityWebRequest request = new UnityWebRequest(url, "POST"))
        {
            byte[] bodyRaw = Encoding.UTF8.GetBytes(jsonData);
            request.uploadHandler = new UploadHandlerRaw(bodyRaw);
            request.downloadHandler = new DownloadHandlerBuffer();
            request.SetRequestHeader("Content-Type", "application/json");

            yield return request.SendWebRequest();

            if (request.result == UnityWebRequest.Result.Success)
            {
                string responseText = request.downloadHandler.text;
                Debug.Log($"Response: {responseText}");

                try
                {
                    SessionTurnResponse response = JsonUtility.FromJson<SessionTurnResponse>(responseText);
                    onSuccess?.Invoke(response);
                }
                catch (Exception e)
                {
                    onError?.Invoke($"Failed to parse response: {e.Message}");
                }
            }
            else
            {
                string errorMsg = $"HTTP Error: {request.error}";
                Debug.LogError(errorMsg);
                onError?.Invoke(errorMsg);
            }
        }
    }
}