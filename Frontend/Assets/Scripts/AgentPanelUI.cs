using UnityEngine;
using UnityEngine.UI;
using TMPro;

public class AgentPanelUI : MonoBehaviour
{
    [SerializeField] private string agentId;
    [SerializeField] private TMP_Text agentNameText;
    [SerializeField] private TMP_Text agentRoleText;
    [SerializeField] private TMP_Text messageText;
    [SerializeField] private Image portraitImage;

    public string AgentId => agentId;

    public void SetMessage(AgentMessage msg)
    {
        if (agentNameText != null)
            agentNameText.text = msg.agent_name;

        if (agentRoleText != null)
            agentRoleText.text = msg.agent_role;

        if (messageText != null)
            messageText.text = msg.text;

        Debug.Log($"Displaying message for {msg.agent_id}: {msg.text}");
    }

    public void Clear()
    {
        if (agentNameText != null)
            agentNameText.text = "";

        if (agentRoleText != null)
            agentRoleText.text = "";

        if (messageText != null)
            messageText.text = "";
    }
}