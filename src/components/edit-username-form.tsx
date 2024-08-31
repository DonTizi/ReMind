import React, { useEffect, useState } from "react";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { ModeToggle } from "./mode-toggle";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";

const formSchema = z.object({
  username: z.string().min(2, {
    message: "Name must be at least 2 characters.",
  }),
});

interface EditUsernameFormProps {
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
}

export default function EditUsernameForm({ setOpen }: EditUsernameFormProps) {
  const [name, setName] = useState("");
  const [loadingAction, setLoadingAction] = useState<string | null>(null);
  const [isBlocking, setIsBlocking] = useState(false);

  useEffect(() => {
    setName(localStorage.getItem("ollama_user") || "Anonymous");
  }, []);

  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (isBlocking) {
        e.preventDefault();
        e.returnValue = '';
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [isBlocking]);

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      username: "",
    },
  });

  function onSubmit(values: z.infer<typeof formSchema>) {
    localStorage.setItem("ollama_user", values.username);
    window.dispatchEvent(new Event("storage"));
    toast.success("Name updated successfully");
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    form.setValue("username", e.currentTarget.value);
    setName(e.currentTarget.value);
  };

  const handleServiceAction = async (action: string) => {
    if (action === 'start') {
      // Envoyer la notification immédiatement après le clic sur le bouton
      toast.success("Service Starting... Please wait a few seconds.");

      // Ensuite, appeler l'API sans bloquer l'interface
      try {
        const response = await fetch(`/api/${action}-service`);
        const data = await response.json();
        if (!response.ok) {
          toast.error(data.message || "Failed to start service");
        }
      } catch (error) {
        toast.error("An error occurred while starting the service");
      }
      return;
    }

    // Pour les autres actions, conserver le comportement existant
    setLoadingAction(action);
    setIsBlocking(true);
    try {
      const response = await fetch(`/api/${action}-service`);
      const data = await response.json();
      if (response.ok) {
        toast.success(data.message);
      } else {
        toast.error(data.message);
      }
    } catch (error) {
      if (error instanceof Error) {
        toast.error(`Error: ${error.message}`);
      } else {
        toast.error('An unknown error occurred');
      }
    } finally {
      setLoadingAction(null);
      setIsBlocking(false);
    }
  };

  const renderButton = (action: string, label: string) => (
    <Button 
      onClick={() => handleServiceAction(action)} 
      disabled={loadingAction !== null && action !== 'start'}
      className="w-full"
    >
      {loadingAction === action && action !== 'start' ? (
        <>
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          {`${label}ing...`}
        </>
      ) : (
        `${label} Service`
      )}
    </Button>
  );

  return (
    <div className="w-full p-6 bg-background border border-border">
      <Form {...form}>
        <div className="w-full flex flex-col gap-4 mb-6">
          <FormLabel>Theme</FormLabel>
          <ModeToggle />
        </div>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
        </form>
        <div className="mt-6 grid grid-cols-3 gap-4">
          {renderButton('install', 'Install')}
          {renderButton('uninstall', 'Uninstall')}
          {renderButton('start', 'Start')}
        </div>
      </Form>
      {isBlocking && loadingAction !== 'start' && (
        <div className="fixed inset-0 bg-background/50 flex items-center justify-center">
          <div className="bg-background border border-border p-6 w-[350px]">
            <div className="flex items-center justify-center space-x-2">
              <Loader2 className="h-6 w-4 animate-spin" />
              <p>Action in progress. Please wait until it's completed.</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
