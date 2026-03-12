using UnityEngine;
using UnityEngine.UI;
using TMPro;

public class AgentPanelUI : MonoBehaviour
{
    [SerializeField] private string agentId; // Set in Inspector, e.g., "entrepreneur", "financial_hawk"
    [SerializeField] private TMP_Text agentNameText;
    [SerializeField] private TMP_Text messageText;
    [SerializeField] private Image portraitImage; // Optional

    public string AgentId => agentId;

    //Set the message for this agent panel
    public void SetMessage(AgentMessage msg)
    {
        if (agentNameText != null)
            agentNameText.text = msg.agent_name;

        if (messageText != null)
            messageText.text = msg.text;

        //Optional: Update portrait based on agent_id or emotion
        //For now, just log
        Debug.Log($"Displaying message for {msg.agent_id}: {msg.text}");
    }

    //Clear the panel
    public void Clear()
    {
        if (agentNameText != null)
            agentNameText.text = "";

        if (messageText != null)
            messageText.text = "";

        //Optional: Reset portrait
    }
}