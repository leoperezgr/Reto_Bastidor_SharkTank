using UnityEngine;
using System.Collections.Generic;

public class TestDialogue : MonoBehaviour
{
    public DialogueManager dialogueManager;

    [ContextMenu("Test Mensajes")]
    public void TestMessages()
    {
        var mensajes = new List<AgentMessage>
        {
            new AgentMessage { agent_id = "financial_hawk", agent_name = "Victoria Cross", text = "Tus números no me convencen." },
            new AgentMessage { agent_id = "tech_visionary", agent_name = "Nadia Osei", text = "La tecnología tiene potencial." },
            new AgentMessage { agent_id = "the_shark", agent_name = "Mark Cuban", text = "¿Por qué tú y no otro?" }
        };

        dialogueManager.DisplayMessages(mensajes);
    }
}