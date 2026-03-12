using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using TMPro;

public class SharkTankUIManager : MonoBehaviour
{
    [SerializeField] private ApiClient apiClient;
    [SerializeField] private List<AgentPanelUI> agentPanels; // Assign in Inspector
    [SerializeField] private TMP_InputField userInputField; // For user replies
    [SerializeField] private Button sendButton;

    private string currentSessionId;
    private int currentTurn;

    private Dictionary<string, AgentPanelUI> agentPanelMap = new Dictionary<string, AgentPanelUI>();

    private void Start()
    {
        // Build the map from agentId to panel
        foreach (var panel in agentPanels)
        {
            if (!string.IsNullOrEmpty(panel.AgentId))
            {
                agentPanelMap[panel.AgentId] = panel;
            }
        }

        if (sendButton != null)
            sendButton.onClick.AddListener(SendUserReply);
    }

    // Start a new pitch session
    public void StartPitch()
    {
        // Hardcoded request for demo - replace with actual data
        StartSessionRequest request = new StartSessionRequest
        {
            entrepreneur_name = "Carlos",
            mode = "quick",
            business_idea = new BusinessIdeaData
            {
                name = "SharkLab AI",
                description = "Simulador multiagente para practicar pitches",
                target_market = "Universidades e incubadoras",
                revenue_model = "Licencias SaaS",
                current_traction = "MVP funcional",
                investment_needed = "$150,000",
                use_of_funds = "Producto y expansión"
            },
            judges = new List<JudgeDefinition>
            {
                new JudgeDefinition
                {
                    id = "financial_hawk",
                    name = "Victoria Cross",
                    role = "Venture Capitalist & Financial Expert",
                    goal = "Identify investments with solid unit economics and a clear path to profitability",
                    backstory = "Numbers-focused investor"
                },
                new JudgeDefinition
                {
                    id = "tech_visionary",
                    name = "Nadia Osei",
                    role = "Deep Tech Investor & Former CTO",
                    goal = "Identify technology with genuine defensibility and the engineering team to scale it",
                    backstory = "Technical and scalability-focused investor"
                }
            }
        };

        apiClient.StartSession(request, OnSessionStarted, OnApiError);
    }

    // Send user reply
    public void SendUserReply()
    {
        if (string.IsNullOrEmpty(currentSessionId))
        {
            Debug.LogError("No active session to send reply.");
            return;
        }

        string userMessage = userInputField != null ? userInputField.text : "";
        if (string.IsNullOrEmpty(userMessage))
        {
            Debug.LogWarning("User message is empty.");
            return;
        }

        NextTurnRequest request = new NextTurnRequest
        {
            session_id = currentSessionId,
            user_message = userMessage
        };

        apiClient.NextTurn(request, OnNextTurnReceived, OnApiError);

        // Clear input
        if (userInputField != null) userInputField.text = "";
    }

    // Render messages from response
    public void RenderMessages(SessionTurnResponse response)
    {
        // Clear all panels first
        foreach (var panel in agentPanels)
        {
            panel.Clear();
        }

        // Render each message
        foreach (var msg in response.messages)
        {
            if (agentPanelMap.TryGetValue(msg.agent_id, out AgentPanelUI panel))
            {
                panel.SetMessage(msg);
            }
            else
            {
                Debug.LogWarning($"No panel found for agent_id: {msg.agent_id}");
            }
        }

        // Update session state
        currentSessionId = response.session_id;
        currentTurn = response.turn;

        Debug.Log($"Rendered turn {currentTurn} for session {currentSessionId}");
    }

    private void OnSessionStarted(SessionTurnResponse response)
    {
        Debug.Log("Session started successfully.");
        RenderMessages(response);
    }

    private void OnNextTurnReceived(SessionTurnResponse response)
    {
        Debug.Log("Next turn received.");
        RenderMessages(response);
    }

    private void OnApiError(string error)
    {
        Debug.LogError($"API Error: {error}");
        // Optional: Show error UI
    }
}