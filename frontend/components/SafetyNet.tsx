'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { motion, AnimatePresence } from 'framer-motion';

interface EmergencyContact {
  name: string;
  phone: string;
  relationship: string;
}

// In a real app, these would come from a user's profile or settings
const mockEmergencyContacts: EmergencyContact[] = [
  { name: 'Dr. Sarah Johnson', phone: '(555) 123-4567', relationship: 'Therapist' },
  { name: 'Michael Smith', phone: '(555) 987-6543', relationship: 'Family' },
];

const emergencyResources = [
  { name: 'National Suicide Prevention Lifeline', phone: '1-800-273-8255', available: '24/7' },
  { name: 'Crisis Text Line', phone: 'Text HOME to 741741', available: '24/7' },
  { name: 'Emergency Services', phone: '911', available: '24/7' },
];

export function SafetyNet() {
  const [isOpen, setIsOpen] = useState(false);
  const [showContacts, setShowContacts] = useState(false);
  
  return (
    <>
      <Button 
        variant="outline" 
        className="fixed bottom-6 right-6 z-50 rounded-full p-3 bg-background shadow-lg hover:shadow-xl hover:bg-red-50 dark:hover:bg-red-950/30 border-2 border-red-500/50 hover:border-red-500"
        onClick={() => setIsOpen(true)}
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-6 w-6 text-red-500"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M13 10V3L4 14h7v7l9-11h-7z"
          />
        </svg>
        <span className="sr-only">Emergency Help</span>
      </Button>

      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent className="sm:max-w-md border-red-400/20 shadow-lg">
          <DialogHeader>
            <DialogTitle className="text-xl font-bold text-red-500">
              Emergency Resources
            </DialogTitle>
            <DialogDescription>
              If you're experiencing a mental health emergency, please reach out for help immediately.
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 my-2">
            <AnimatePresence mode="wait">
              {!showContacts ? (
                <motion.div
                  key="resources"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.2 }}
                >
                  <Card className="border-red-400/20">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-lg">Crisis Helplines</CardTitle>
                    </CardHeader>
                    <CardContent className="pb-2">
                      <ul className="space-y-2">
                        {emergencyResources.map((resource) => (
                          <li key={resource.name} className="flex justify-between items-center text-sm">
                            <div>
                              <p>{resource.name}</p>
                              <p className="text-xs text-muted-foreground">{resource.available}</p>
                            </div>
                            <Button 
                              variant="ghost" 
                              size="sm" 
                              className="text-primary hover:text-primary/80"
                              asChild
                            >
                              <a href={`tel:${resource.phone.replace(/\D/g, '')}`}>
                                {resource.phone}
                              </a>
                            </Button>
                          </li>
                        ))}
                      </ul>
                    </CardContent>
                    <CardFooter>
                      <Button
                        variant="outline"
                        onClick={() => setShowContacts(true)}
                        className="w-full text-sm"
                      >
                        View Your Emergency Contacts
                      </Button>
                    </CardFooter>
                  </Card>
                </motion.div>
              ) : (
                <motion.div
                  key="contacts"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.2 }}
                >
                  <Card className="border-red-400/20">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-lg">Your Emergency Contacts</CardTitle>
                      <CardDescription>People you've designated to help in a crisis</CardDescription>
                    </CardHeader>
                    <CardContent className="pb-2">
                      {mockEmergencyContacts.length > 0 ? (
                        <ul className="space-y-3">
                          {mockEmergencyContacts.map((contact) => (
                            <li key={contact.name} className="flex justify-between items-center text-sm">
                              <div>
                                <p>{contact.name}</p>
                                <p className="text-xs text-muted-foreground">{contact.relationship}</p>
                              </div>
                              <Button
                                variant="ghost"
                                size="sm"
                                className="text-primary hover:text-primary/80"
                                asChild
                              >
                                <a href={`tel:${contact.phone.replace(/\D/g, '')}`}>
                                  {contact.phone}
                                </a>
                              </Button>
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <p className="text-sm text-muted-foreground text-center py-4">
                          You haven't added any emergency contacts yet.
                        </p>
                      )}
                    </CardContent>
                    <CardFooter>
                      <Button
                        variant="outline"
                        onClick={() => setShowContacts(false)}
                        className="w-full text-sm"
                      >
                        Back to Crisis Resources
                      </Button>
                    </CardFooter>
                  </Card>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
          
          <DialogFooter className="sm:justify-start">
            <div className="w-full text-center text-xs text-muted-foreground">
              If you're in immediate danger, please call emergency services (911) right away.
            </div>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
} 